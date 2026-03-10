#!/usr/bin/env python3
"""
Trigger sources and success: trigger taxonomy, trigger × segment (normalized % per agent), RF + SHAP.
Normalize each agent's run counts by trigger to percentages (sum to 100%). Resample if success/failure imbalanced.
Outputs: taxonomy CSV, trigger × segment table, RF importance + SHAP summary, bar chart, SHAP plot.
"""
import yaml
import duckdb
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.utils import resample
import shap

from _utils import REPO_ROOT, DATA_DIR, OUTPUT_DIR, get_connection, load_csv_as_view, ensure_output_dir


def load_config():
    with open(REPO_ROOT / "analysis" / "config.yaml") as f:
        return yaml.safe_load(f)


def main():
    ensure_output_dir()
    config = load_config()
    con = get_connection()

    # Load cohort and runs
    cohort_path = OUTPUT_DIR / "cohort.csv"
    if not cohort_path.exists():
        raise FileNotFoundError("Run define_success_cohort.py first to create cohort.csv")
    cohort_df = pd.read_csv(cohort_path)

    load_csv_as_view(con, "super_agent_run", DATA_DIR / "super_agent_run.csv")
    con.register("cohort_df", cohort_df)

    # Trigger taxonomy: use TRIGGER_SOURCE (normalize \N to 'unknown')
    con.execute(
        """
        CREATE OR REPLACE TEMP VIEW run_trigger AS
        SELECT
            AGENT_ID,
            RUN_ID,
            CASE WHEN TRIM(TRIGGER_SOURCE) = '' OR TRIGGER_SOURCE = '\\\\N' THEN 'unknown'
                 ELSE TRIM(TRIGGER_SOURCE) END AS trigger_source
        FROM super_agent_run
        """
    )

    # Per-agent run counts by trigger
    trigger_counts = con.execute(
        """
        SELECT c.AGENT_ID, c.success_segment, r.trigger_source, count(*) AS run_count
        FROM cohort_df c
        JOIN run_trigger r ON r.AGENT_ID = c.AGENT_ID
        GROUP BY c.AGENT_ID, c.success_segment, r.trigger_source
        """
    ).fetchdf()

    # Pivot to get each agent's run count per trigger, then normalize to %
    agent_total = trigger_counts.groupby("AGENT_ID")["run_count"].transform("sum")
    trigger_counts["pct"] = trigger_counts["run_count"] / agent_total * 100
    wide = trigger_counts.pivot_table(
        index=["AGENT_ID", "success_segment"],
        columns="trigger_source",
        values="pct",
        aggfunc="sum",
    ).fillna(0)

    # Taxonomy (total run counts by trigger)
    taxonomy = (
        trigger_counts.groupby("trigger_source")["run_count"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    taxonomy.columns = ["trigger_source", "total_runs"]
    taxonomy.to_csv(OUTPUT_DIR / "trigger_taxonomy.csv", index=False)
    print("Trigger taxonomy:")
    print(taxonomy.to_string(index=False))

    # Trigger × segment (mean % per agent)
    wide_reset = wide.reset_index()
    trigger_by_segment = (
        wide_reset.groupby("success_segment")[taxonomy["trigger_source"].tolist()]
        .mean()
        .T
    )
    trigger_by_segment.to_csv(OUTPUT_DIR / "trigger_by_segment.csv")
    print("\nTrigger × segment (mean % per agent):")
    print(trigger_by_segment.round(2).to_string())

    # RF + SHAP: predict success vs non-success (failure + dormant); use normalized trigger %
    X = wide_reset.drop(columns=["AGENT_ID", "success_segment"])
    y = (wide_reset["success_segment"] == "success").astype(int)
    X = X.reindex(columns=sorted(X.columns), fill_value=0)

    # Resample if imbalanced (e.g. if success < 20% or > 80% of sample)
    if y.mean() < 0.2 or y.mean() > 0.8:
        df_bal = wide_reset.copy()
        df_bal["_target"] = y
        minority = df_bal[df_bal["_target"] == 1]
        majority = df_bal[df_bal["_target"] == 0]
        n_min = len(minority)
        n_maj = len(majority)
        if n_min < n_maj:
            majority = resample(majority, replace=False, n_samples=min(n_maj, n_min * 3), random_state=42)
        else:
            minority = resample(minority, replace=False, n_samples=min(n_min, n_maj * 3), random_state=42)
        balanced = pd.concat([minority, majority], ignore_index=True)
        X = balanced.drop(columns=["AGENT_ID", "success_segment", "_target"])
        y = balanced["_target"]
        X = X.reindex(columns=sorted([c for c in X.columns if c in wide_reset.columns]), fill_value=0)
        print("\nResampled for class balance; new sample size:", len(X))

    model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    model.fit(X, y)
    importance = pd.DataFrame(
        {"feature": X.columns, "importance": model.feature_importances_}
    ).sort_values("importance", ascending=False)
    importance.to_csv(OUTPUT_DIR / "trigger_rf_importance.csv", index=False)
    print("\nRF feature importance (top 10):")
    print(importance.head(10).to_string(index=False))

    # SHAP (sample for speed if large)
    sample_size = min(500, len(X))
    X_shap = X.sample(n=sample_size, random_state=42) if len(X) > sample_size else X
    explainer = shap.TreeExplainer(model, X_shap)
    shaps = explainer.shap_values(X_shap)
    if isinstance(shaps, list):
        shaps = shaps[1]  # class 1 (success)
    if shaps.ndim == 3:
        shaps = shaps[:, :, 1]  # (n_samples, n_features)
    mean_abs = np.abs(shaps).mean(axis=0)
    mean_signed = shaps.mean(axis=0)
    shap_summary = pd.DataFrame(
        {"mean_abs_shap": mean_abs, "mean_shap": mean_signed},
        index=X.columns,
    ).sort_values("mean_abs_shap", ascending=False)
    shap_summary.to_csv(OUTPUT_DIR / "trigger_shap_summary.csv")
    shap_direction = shap_summary.reset_index()
    shap_direction.columns = ["feature", "mean_abs_shap", "mean_shap"]
    shap_direction = shap_direction[["feature", "mean_shap", "mean_abs_shap"]]
    shap_direction.to_csv(OUTPUT_DIR / "trigger_shap_direction.csv", index=False)
    print("\nSHAP mean |impact| (top 10):")
    print(shap_summary.head(10).to_string())

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
    pd.DataFrame(shap_by_value_rows).to_csv(OUTPUT_DIR / "trigger_shap_by_value.csv", index=False)

    # Logistic regression (full X, y; standardize for comparable coefficients)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    lr = LogisticRegression(C=1e6, max_iter=1000, random_state=42)
    lr.fit(X_scaled, y)
    lr_coef = pd.DataFrame({"feature": X.columns, "coefficient": lr.coef_[0]})
    lr_coef.to_csv(OUTPUT_DIR / "trigger_logistic_coefficients.csv", index=False)
    print("\nLogistic regression coefficients (top 10 by |coef|):")
    lr_coef["abs_coef"] = np.abs(lr_coef["coefficient"])
    print(lr_coef.nlargest(10, "abs_coef")[["feature", "coefficient"]].to_string(index=False))

    # Bar chart: trigger × segment (mean %)
    fig, ax = plt.subplots(figsize=(10, 5))
    trigger_by_segment.plot(kind="bar", ax=ax, width=0.8)
    ax.set_ylabel("Mean % of runs per agent")
    ax.set_xlabel("Trigger source")
    ax.set_title("Trigger mix by success segment (normalized % per agent)")
    ax.legend(title="Segment")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "trigger_by_segment.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\nWrote {OUTPUT_DIR / 'trigger_by_segment.png'}")

    # SHAP summary plot (bar)
    shap.summary_plot(shaps, X_shap, plot_type="bar", show=False, max_display=15)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "trigger_shap_bar.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Wrote {OUTPUT_DIR / 'trigger_shap_bar.png'}")

    # SHAP beeswarm (direction visible)
    shap.summary_plot(shaps, X_shap, show=False, max_display=15)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "trigger_shap_beeswarm.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Wrote {OUTPUT_DIR / 'trigger_shap_beeswarm.png'}")


if __name__ == "__main__":
    main()
