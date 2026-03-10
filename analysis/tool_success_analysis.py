#!/usr/bin/env python3
"""
ClickUp tools and success: tool taxonomy, tool × segment (normalized = avg tool count per run per agent),
RF + SHAP, cohort comparison (success vs failure) with statistical significance (Mann-Whitney).
Outputs: tool list CSV, tool × segment table, cohort comparison with p-values, RF importance, SHAP, plots.
"""
import duckdb
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from scipy import stats
import shap

from _utils import REPO_ROOT, OUTPUT_DIR, get_connection, load_csv_as_view, ensure_output_dir


def main():
    ensure_output_dir()
    con = get_connection()

    cohort_path = OUTPUT_DIR / "cohort.csv"
    if not cohort_path.exists():
        raise FileNotFoundError("Run define_success_cohort.py first")
    cohort_df = pd.read_csv(cohort_path)
    con.register("cohort_df", cohort_df)

    load_csv_as_view(con, "super_agent_run", REPO_ROOT / "data" / "super_agent_run.csv")
    load_csv_as_view(con, "super_agent_tools", REPO_ROOT / "data" / "super_agent_tools.csv")

    # ClickUp tools only; use CALL_NAME as tool identifier
    con.execute(
        """
        CREATE OR REPLACE TEMP VIEW clickup_tool_calls AS
        SELECT AGENT_ID, RUN_ID, CALL_NAME, 1 AS call_count
        FROM super_agent_tools
        WHERE CALL_TYPE = 'clickup_tool' AND TRIM(COALESCE(CALL_NAME, '')) != ''
        """
    )

    # Run count per agent (from runs that have at least one clickup tool call, or all runs?)
    # Plan: for each agent, run_count = count of distinct RUN_ID in super_agent_run; tool count = sum of calls per CALL_NAME in those runs.
    # We need: agent, run_count, per-tool total calls. Then avg_per_run = total_calls / run_count.
    run_count = con.execute(
        """
        SELECT r.AGENT_ID, count(DISTINCT r.RUN_ID) AS run_count
        FROM super_agent_run r
        JOIN cohort_df c ON c.AGENT_ID = r.AGENT_ID
        GROUP BY r.AGENT_ID
        """
    ).fetchdf()

    tool_totals = con.execute(
        """
        SELECT t.AGENT_ID, t.CALL_NAME, count(*) AS total_calls
        FROM cohort_df c
        JOIN clickup_tool_calls t ON t.AGENT_ID = c.AGENT_ID
        GROUP BY t.AGENT_ID, t.CALL_NAME
        """
    ).fetchdf()

    # Pivot tool_totals to agent × tool (total_calls), then merge cohort + run_count; avg_per_run = total_calls / run_count
    tool_pivot = tool_totals.pivot_table(
        index="AGENT_ID", columns="CALL_NAME", values="total_calls", aggfunc="sum"
    ).fillna(0)
    agent_run = cohort_df[["AGENT_ID", "success_segment"]].merge(run_count, on="AGENT_ID", how="left")
    agent_run["run_count"] = agent_run["run_count"].fillna(0).clip(lower=1)
    wide = agent_run.merge(tool_pivot, on="AGENT_ID", how="left").fillna(0)
    tool_cols = [c for c in wide.columns if c not in ("AGENT_ID", "success_segment", "run_count")]
    for c in tool_cols:
        wide[c] = wide[c] / wide["run_count"]

    # Tool taxonomy (total calls, success rate from IS_SUCCESS if we have it - optional)
    taxonomy = (
        tool_totals.groupby("CALL_NAME")["total_calls"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    taxonomy.columns = ["tool_name", "total_calls"]
    taxonomy.to_csv(OUTPUT_DIR / "tool_taxonomy.csv", index=False)
    print("Tool taxonomy (top 15):")
    print(taxonomy.head(15).to_string(index=False))

    tool_by_segment = wide.groupby("success_segment")[tool_cols].mean().T
    tool_by_segment.to_csv(OUTPUT_DIR / "tool_by_segment.csv")
    print("\nTool × segment (mean avg per run, top 10 tools):")
    print(tool_by_segment.head(10).round(4).to_string())

    # Cohort comparison: success vs failure, mean per tool + Mann-Whitney p-value
    success_agents = wide[wide["success_segment"] == "success"]
    failure_agents = wide[wide["success_segment"] == "failure"]
    cohort_comp = []
    for col in tool_cols:
        s = success_agents[col].values
        f = failure_agents[col].values
        if len(s) < 2 or len(f) < 2:
            p = np.nan
        else:
            _, p = stats.mannwhitneyu(s, f, alternative="two-sided")
        cohort_comp.append({
            "tool": col,
            "mean_success": s.mean(),
            "mean_failure": f.mean(),
            "p_value": p,
        })
    cohort_comp_df = pd.DataFrame(cohort_comp).sort_values("p_value")
    cohort_comp_df.to_csv(OUTPUT_DIR / "tool_cohort_comparison.csv", index=False)
    print("\nCohort comparison (success vs failure) — top 10 by p-value:")
    print(cohort_comp_df.head(10).to_string(index=False))

    # RF + SHAP: predict success vs non-success
    X = wide[tool_cols].fillna(0)
    y = (wide["success_segment"] == "success").astype(int)
    if y.sum() < 10 or (1 - y).sum() < 10:
        print("Skipping RF/SHAP: too few success or failure agents")
    else:
        model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
        model.fit(X, y)
        importance = pd.DataFrame(
            {"feature": tool_cols, "importance": model.feature_importances_}
        ).sort_values("importance", ascending=False)
        importance.to_csv(OUTPUT_DIR / "tool_rf_importance.csv", index=False)
        print("\nRF feature importance (top 10):")
        print(importance.head(10).to_string(index=False))

        sample_size = min(500, len(X))
        X_shap = X.sample(n=sample_size, random_state=42) if len(X) > sample_size else X
        explainer = shap.TreeExplainer(model, X_shap)
        shaps = explainer.shap_values(X_shap)
        if isinstance(shaps, list):
            shaps = shaps[1]
        if shaps.ndim == 3:
            shaps = shaps[:, :, 1]
        mean_abs = np.abs(shaps).mean(axis=0)
        mean_signed = shaps.mean(axis=0)
        shap_summary = pd.DataFrame(
            {"mean_abs_shap": mean_abs, "mean_shap": mean_signed},
            index=X_shap.columns,
        ).sort_values("mean_abs_shap", ascending=False)
        shap_summary.to_csv(OUTPUT_DIR / "tool_shap_summary.csv")
        shap_direction = shap_summary.reset_index()
        shap_direction.columns = ["feature", "mean_abs_shap", "mean_shap"]
        shap_direction = shap_direction[["feature", "mean_shap", "mean_abs_shap"]]
        shap_direction.to_csv(OUTPUT_DIR / "tool_shap_direction.csv", index=False)

        # Average SHAP per feature value (quartile bins)
        shap_by_value_rows = []
        for col in X_shap.columns:
            vals = X_shap[col].values
            qs = np.percentile(vals, [25, 50, 75])
            for i, (lo, hi, label) in enumerate([
                (None, qs[0], "q1"), (qs[0], qs[1], "q2"), (qs[1], qs[2], "q3"), (qs[2], None, "q4")
            ]):
                if lo is None:
                    mask = vals <= hi
                elif hi is None:
                    mask = vals > lo
                else:
                    mask = (vals > lo) & (vals <= hi)
                if mask.sum() == 0:
                    continue
                col_idx = list(X_shap.columns).index(col)
                shap_by_value_rows.append({
                    "feature": col,
                    "value_bin": label,
                    "mean_shap": float(shaps[mask, col_idx].mean()),
                    "n_agents": int(mask.sum()),
                })
        pd.DataFrame(shap_by_value_rows).to_csv(OUTPUT_DIR / "tool_shap_by_value.csv", index=False)

        # Logistic regression (full X, y; standardize)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        lr = LogisticRegression(C=1e6, max_iter=1000, random_state=42)
        lr.fit(X_scaled, y)
        lr_coef = pd.DataFrame({"feature": X.columns, "coefficient": lr.coef_[0]})
        lr_coef.to_csv(OUTPUT_DIR / "tool_logistic_coefficients.csv", index=False)
        print("\nLogistic regression coefficients (top 10 by |coef|):")
        lr_coef["abs_coef"] = np.abs(lr_coef["coefficient"])
        print(lr_coef.nlargest(10, "abs_coef")[["feature", "coefficient"]].to_string(index=False))

        shap.summary_plot(shaps, X_shap, plot_type="bar", show=False, max_display=15)
        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / "tool_shap_bar.png", dpi=150, bbox_inches="tight")
        plt.close()
        print(f"Wrote {OUTPUT_DIR / 'tool_shap_bar.png'}")

        # SHAP beeswarm
        shap.summary_plot(shaps, X_shap, show=False, max_display=15)
        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / "tool_shap_beeswarm.png", dpi=150, bbox_inches="tight")
        plt.close()
        print(f"Wrote {OUTPUT_DIR / 'tool_shap_beeswarm.png'}")

    # Bar chart: top tools by mean avg per run for success vs failure
    top_tools = taxonomy.head(12)["tool_name"].tolist()
    top_tools_in_wide = [t for t in top_tools if t in wide.columns]
    seg_means = wide.groupby("success_segment")[top_tools_in_wide].mean()
    fig, ax = plt.subplots(figsize=(12, 5))
    n = len(top_tools_in_wide)
    x = np.arange(n)
    w = 0.35
    ax.bar(x - w/2, seg_means.loc["success"].values if "success" in seg_means.index else np.zeros(n), w, label="success")
    ax.bar(x + w/2, seg_means.loc["failure"].values if "failure" in seg_means.index else np.zeros(n), w, label="failure")
    ax.set_xticks(x)
    ax.set_xticklabels([t[:20] + ".." if len(t) > 20 else t for t in top_tools_in_wide], rotation=45, ha="right")
    ax.set_ylabel("Mean avg per run")
    ax.set_title("Top ClickUp tools: success vs failure (avg calls per run)")
    ax.legend()
    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "tool_by_segment.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Wrote {OUTPUT_DIR / 'tool_by_segment.png'}")


if __name__ == "__main__":
    main()
