#!/usr/bin/env python3
"""
Prompts (classifications) and success: one-hot encode classification dimensions (exclude business_items),
add trigger type and template (custom/templated) from run data. RF + SHAP, per-dimension and trigger/template × segment.
Scope: only agent_ids in agent_classifications.csv.
"""
import duckdb
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import shap

from _utils import REPO_ROOT, DATA_DIR, OUTPUT_DIR, get_connection, load_csv_as_view, ensure_output_dir


# Classification dimensions to use (exclude business_items)
CLASS_DIMS = [
    "team_orientation", "domain_knowledge_depth", "operational_scope", "data_flow_direction",
    "autonomy_level", "functional_archetype", "tone_and_persona", "execution_dataset",
    "state_persistence", "external_integration_scope", "output_modality",
    "domain_industry_vertical", "use_case_context", "implied_end_date",
]


def main():
    ensure_output_dir()
    con = get_connection()

    cohort_path = OUTPUT_DIR / "cohort.csv"
    if not cohort_path.exists():
        raise FileNotFoundError("Run define_success_cohort.py first")
    cohort_df = pd.read_csv(cohort_path)
    con.register("cohort_df", cohort_df)

    load_csv_as_view(con, "super_agent_run", DATA_DIR / "super_agent_run.csv")
    load_csv_as_view(con, "agent_classifications", DATA_DIR / "agent_classifications.csv")

    # Restrict cohort to agents that have classifications
    classified_agents = con.execute(
        "SELECT DISTINCT agent_id FROM agent_classifications"
    ).fetchdf()
    cohort_class = cohort_df[cohort_df["AGENT_ID"].isin(classified_agents["agent_id"])].copy()
    cohort_class = cohort_class.rename(columns={"AGENT_ID": "agent_id"})
    print(f"Agents in cohort with classifications: {len(cohort_class):,}")

    # Load classifications and merge segment
    ac = pd.read_csv(DATA_DIR / "agent_classifications.csv")
    ac = ac.drop(columns=["business_items"], errors="ignore")
    ac = ac.merge(cohort_class[["agent_id", "success_segment"]], on="agent_id", how="inner")

    # One-hot encode classification dimensions (keep unknown as a category)
    onehot_list = []
    for col in CLASS_DIMS:
        if col not in ac.columns:
            continue
        dummies = pd.get_dummies(ac[col].fillna("unknown").astype(str), prefix=col, prefix_sep="=")
        onehot_list.append(dummies)
    X_class = pd.concat(onehot_list, axis=1)
    X_class = X_class.reindex(columns=sorted(X_class.columns), fill_value=0)

    # Prompts-only model: classifications only (no trigger/template)
    X_prompts_only = pd.concat([ac[["agent_id", "success_segment"]], X_class], axis=1)
    feature_cols_prompts_only = X_class.columns.tolist()
    X_only = X_prompts_only[feature_cols_prompts_only]
    y_only = (X_prompts_only["success_segment"] == "success").astype(int)
    if y_only.sum() >= 10 and (1 - y_only).sum() >= 10:
        model_po = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
        model_po.fit(X_only, y_only)
        importance_po = pd.DataFrame(
            {"feature": feature_cols_prompts_only, "importance": model_po.feature_importances_}
        ).sort_values("importance", ascending=False)
        importance_po.to_csv(OUTPUT_DIR / "classification_prompts_only_rf_importance.csv", index=False)
        # SHAP on full cohort: all agents in agent_classifications (~114K). Use a background sample for TreeExplainer to save memory; shap_values(X_only) returns SHAP for every agent.
        n_agents_full = len(X_only)
        print(f"Prompts-only SHAP: full classified cohort N = {n_agents_full:,} agents (no 500 limit). Computing SHAP for all agents...")
        background_size = min(2000, n_agents_full)
        X_background = X_only.sample(n=background_size, random_state=42) if n_agents_full > background_size else X_only
        explainer_po = shap.TreeExplainer(model_po, X_background)
        shaps_po = explainer_po.shap_values(X_only)  # SHAP for every row in X_only (~114K)
        if isinstance(shaps_po, list):
            shaps_po = shaps_po[1]
        if shaps_po.ndim == 3:
            shaps_po = shaps_po[:, :, 1]
        print(f"SHAP matrix shape: {shaps_po.shape[0]:,} agents x {shaps_po.shape[1]} features.")
        mean_abs_po = np.abs(shaps_po).mean(axis=0)
        mean_signed_po = shaps_po.mean(axis=0)
        shap_dir_po = pd.DataFrame(
            {"feature": X_only.columns, "mean_shap": mean_signed_po, "mean_abs_shap": mean_abs_po}
        )
        shap_dir_po.to_csv(OUTPUT_DIR / "classification_prompts_only_shap_direction.csv", index=False)
        shap_by_val_po = []
        for col in X_only.columns:
            col_idx = list(X_only.columns).index(col)
            for val in [0, 1]:
                mask = (X_only[col].values == val)
                if mask.sum() == 0:
                    continue
                shap_by_val_po.append({
                    "feature": col, "value": int(val),
                    "mean_shap": float(shaps_po[mask, col_idx].mean()),
                    "n_agents": int(mask.sum()),
                })
        pd.DataFrame(shap_by_val_po).to_csv(OUTPUT_DIR / "classification_prompts_only_shap_by_value.csv", index=False)
        scaler_po = StandardScaler()
        X_only_scaled = scaler_po.fit_transform(X_only)
        lr_po = LogisticRegression(C=1e6, max_iter=1000, random_state=42)
        lr_po.fit(X_only_scaled, y_only)
        pd.DataFrame({"feature": X_only.columns, "coefficient": lr_po.coef_[0]}).to_csv(
            OUTPUT_DIR / "classification_prompts_only_logistic_coefficients.csv", index=False
        )
        n_features_po = len(feature_cols_prompts_only)
        shap.summary_plot(shaps_po, X_only, plot_type="bar", show=False, max_display=n_features_po)
        fig = plt.gcf()
        fig.set_size_inches(10, max(8, n_features_po * 0.22))
        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / "classification_prompts_only_shap_bar.png", dpi=150, bbox_inches="tight")
        plt.close()
        shap.summary_plot(shaps_po, X_only, show=False, max_display=n_features_po)
        fig = plt.gcf()
        fig.set_size_inches(10, max(8, n_features_po * 0.22))
        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / "classification_prompts_only_shap_beeswarm.png", dpi=150, bbox_inches="tight")
        plt.close()
        print(f"Wrote classification_prompts_only_* outputs (SHAP on full cohort, N={shaps_po.shape[0]:,} agents).")

    # Trigger: primary trigger per agent from runs (for classified agents only)
    run_trigger = con.execute(
        """
        SELECT AGENT_ID,
               COALESCE(NULLIF(TRIM(TRIGGER_SOURCE), ''), 'unknown') AS trigger_source,
               count(*) AS run_count
        FROM super_agent_run
        WHERE AGENT_ID IN (SELECT agent_id FROM agent_classifications)
        GROUP BY AGENT_ID, TRIGGER_SOURCE
        """
    ).fetchdf()
    primary_trigger = (
        run_trigger.sort_values("run_count", ascending=False)
        .groupby("AGENT_ID")
        .first()
        .reset_index()[["AGENT_ID", "trigger_source"]]
    )
    primary_trigger = primary_trigger.rename(columns={"AGENT_ID": "agent_id"})
    ac = ac.merge(primary_trigger, on="agent_id", how="left")
    ac["trigger_source"] = ac["trigger_source"].fillna("unknown")

    # Template: TEMPLATE_TYPE from runs (mode per agent)
    run_template = con.execute(
        """
        SELECT AGENT_ID, TEMPLATE_TYPE, count(*) AS run_count
        FROM super_agent_run
        WHERE AGENT_ID IN (SELECT agent_id FROM agent_classifications)
        GROUP BY AGENT_ID, TEMPLATE_TYPE
        """
    ).fetchdf()
    run_template["TEMPLATE_TYPE"] = run_template["TEMPLATE_TYPE"].fillna("unknown").astype(str).str.strip()
    primary_template = (
        run_template.sort_values("run_count", ascending=False)
        .groupby("AGENT_ID")
        .first()
        .reset_index()[["AGENT_ID", "TEMPLATE_TYPE"]]
    )
    primary_template = primary_template.rename(columns={"AGENT_ID": "agent_id"})
    ac = ac.merge(primary_template, on="agent_id", how="left")
    ac["TEMPLATE_TYPE"] = ac["TEMPLATE_TYPE"].fillna("unknown").astype(str).str.strip()
    ac.loc[ac["TEMPLATE_TYPE"] == "", "TEMPLATE_TYPE"] = "unknown"

    # Custom vs templated (high-level) + template sub-type (one-hot of TEMPLATE_TYPE)
    ac["template_is_custom"] = (ac["TEMPLATE_TYPE"] == "custom").astype(int)
    ac["template_is_templated"] = (~ac["TEMPLATE_TYPE"].isin(["custom", "unknown"])).astype(int)

    # Template taxonomy: type, run_count, agent_count, segment counts
    run_tax = run_template.groupby("TEMPLATE_TYPE")["run_count"].sum().reset_index()
    run_tax.columns = ["template_type", "total_runs"]
    agent_tax = ac.groupby("TEMPLATE_TYPE").agg(agent_count=("agent_id", "count")).reset_index()
    agent_tax.columns = ["template_type", "agent_count"]
    template_taxonomy = run_tax.merge(agent_tax, on="template_type", how="outer").fillna(0)
    seg = ac.groupby("TEMPLATE_TYPE")["success_segment"].value_counts().unstack(fill_value=0)
    for col in ["dormant", "failure", "success"]:
        if col in seg.columns:
            template_taxonomy[col] = template_taxonomy["template_type"].map(seg[col].to_dict()).fillna(0).astype(int)
    template_taxonomy.to_csv(OUTPUT_DIR / "classification_template_taxonomy.csv", index=False)

    # Sub-type dummies (template=custom, template=unknown, template=<other>, ...)
    template_dum = pd.get_dummies(ac["TEMPLATE_TYPE"], prefix="template", prefix_sep="=")
    template_extra = ac[["template_is_custom", "template_is_templated"]]
    # Full feature matrix: classifications + trigger + custom/templated flags + template sub-types
    trigger_dum = pd.get_dummies(ac["trigger_source"], prefix="trigger", prefix_sep="=")
    X_full = pd.concat([ac[["agent_id", "success_segment"]], X_class, trigger_dum, template_extra, template_dum], axis=1)
    X_full = X_full.fillna(0)
    feature_cols = [c for c in X_full.columns if c not in ("agent_id", "success_segment")]
    X = X_full[feature_cols].fillna(0).astype(float)
    y = (X_full["success_segment"] == "success").astype(int)

    # Templates-only model: custom vs templated + template sub-types (no trigger, no classifications)
    X_templates_only = pd.concat([ac[["agent_id", "success_segment"]], template_extra, template_dum], axis=1)
    feature_cols_templates_only = list(template_extra.columns) + template_dum.columns.tolist()
    X_tmp = X_templates_only[feature_cols_templates_only].astype(float)
    y_tmp = (X_templates_only["success_segment"] == "success").astype(int)
    if y_tmp.sum() >= 10 and (1 - y_tmp).sum() >= 10 and len(feature_cols_templates_only) >= 1:
        model_tmp = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
        model_tmp.fit(X_tmp, y_tmp)
        importance_tmp = pd.DataFrame(
            {"feature": feature_cols_templates_only, "importance": model_tmp.feature_importances_}
        ).sort_values("importance", ascending=False)
        importance_tmp.to_csv(OUTPUT_DIR / "classification_templates_only_rf_importance.csv", index=False)
        sample_size_tmp = min(500, len(X_tmp))
        X_shap_tmp = X_tmp.sample(n=sample_size_tmp, random_state=42) if len(X_tmp) > sample_size_tmp else X_tmp
        explainer_tmp = shap.TreeExplainer(model_tmp, X_shap_tmp)
        shaps_tmp = explainer_tmp.shap_values(X_shap_tmp)
        if isinstance(shaps_tmp, list):
            shaps_tmp = shaps_tmp[1]
        if shaps_tmp.ndim == 3:
            shaps_tmp = shaps_tmp[:, :, 1]
        shap_dir_tmp = pd.DataFrame(
            {"feature": X_shap_tmp.columns, "mean_shap": shaps_tmp.mean(axis=0), "mean_abs_shap": np.abs(shaps_tmp).mean(axis=0)}
        )
        shap_dir_tmp.to_csv(OUTPUT_DIR / "classification_templates_only_shap_direction.csv", index=False)
        shap_by_val_tmp = []
        for col in X_shap_tmp.columns:
            col_idx = list(X_shap_tmp.columns).index(col)
            for val in [0, 1]:
                mask = (X_shap_tmp[col].values == val)
                if mask.sum() == 0:
                    continue
                shap_by_val_tmp.append({
                    "feature": col, "value": int(val),
                    "mean_shap": float(shaps_tmp[mask, col_idx].mean()),
                    "n_agents": int(mask.sum()),
                })
        pd.DataFrame(shap_by_val_tmp).to_csv(OUTPUT_DIR / "classification_templates_only_shap_by_value.csv", index=False)
        scaler_tmp = StandardScaler()
        X_tmp_scaled = scaler_tmp.fit_transform(X_tmp)
        lr_tmp = LogisticRegression(C=1e6, max_iter=1000, random_state=42)
        lr_tmp.fit(X_tmp_scaled, y_tmp)
        pd.DataFrame({"feature": X_tmp.columns, "coefficient": lr_tmp.coef_[0]}).to_csv(
            OUTPUT_DIR / "classification_templates_only_logistic_coefficients.csv", index=False
        )
        shap.summary_plot(shaps_tmp, X_shap_tmp, plot_type="bar", show=False, max_display=20)
        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / "classification_templates_only_shap_bar.png", dpi=150, bbox_inches="tight")
        plt.close()
        shap.summary_plot(shaps_tmp, X_shap_tmp, show=False, max_display=20)
        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / "classification_templates_only_shap_beeswarm.png", dpi=150, bbox_inches="tight")
        plt.close()
        print("Wrote classification_templates_only_* outputs")

    # Per-dimension: value × segment counts and success rate
    coverage = X_full["success_segment"].value_counts()
    coverage.to_csv(OUTPUT_DIR / "classification_coverage.csv")
    print("\nClassification cohort by segment:")
    print(coverage.to_string())

    dim_tables = {}
    for col in CLASS_DIMS:
        if col not in ac.columns:
            continue
        tab = ac.groupby([col, "success_segment"]).size().unstack(fill_value=0)
        tab["success_rate"] = tab.get("success", 0) / (tab.sum(axis=1) + 1e-9)
        dim_tables[col] = tab
        tab.to_csv(OUTPUT_DIR / f"classification_dim_{col}.csv")

    # Trigger × segment, Template × segment
    trigger_segment = ac.groupby("trigger_source")["success_segment"].value_counts().unstack(fill_value=0)
    trigger_segment.to_csv(OUTPUT_DIR / "classification_trigger_by_segment.csv")
    template_segment = ac.groupby("TEMPLATE_TYPE")["success_segment"].value_counts().unstack(fill_value=0)
    template_segment.to_csv(OUTPUT_DIR / "classification_template_by_segment.csv")

    # RF + SHAP
    if y.sum() < 10 or (1 - y).sum() < 10:
        print("Skipping RF/SHAP: too few success or failure in classified cohort")
    else:
        model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
        model.fit(X, y)
        importance = pd.DataFrame(
            {"feature": feature_cols, "importance": model.feature_importances_}
        ).sort_values("importance", ascending=False)
        importance.to_csv(OUTPUT_DIR / "classification_rf_importance.csv", index=False)
        print("\nRF feature importance (top 15):")
        print(importance.head(15).to_string(index=False))

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
        shap_direction = shap_summary.reset_index()
        shap_direction.columns = ["feature", "mean_abs_shap", "mean_shap"]
        shap_direction = shap_direction[["feature", "mean_shap", "mean_abs_shap"]]
        shap_direction.to_csv(OUTPUT_DIR / "classification_shap_direction.csv", index=False)

        # Average SHAP per feature value (one-hot: value 0 vs 1)
        shap_by_value_rows = []
        for col in X_shap.columns:
            col_idx = list(X_shap.columns).index(col)
            for val in [0, 1]:
                mask = (X_shap[col].values == val)
                if mask.sum() == 0:
                    continue
                shap_by_value_rows.append({
                    "feature": col,
                    "value": int(val),
                    "mean_shap": float(shaps[mask, col_idx].mean()),
                    "n_agents": int(mask.sum()),
                })
        pd.DataFrame(shap_by_value_rows).to_csv(OUTPUT_DIR / "classification_shap_by_value.csv", index=False)

        # Logistic regression (full X, y; standardize)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        lr = LogisticRegression(C=1e6, max_iter=1000, random_state=42)
        lr.fit(X_scaled, y)
        lr_coef = pd.DataFrame({"feature": X.columns, "coefficient": lr.coef_[0]})
        lr_coef.to_csv(OUTPUT_DIR / "classification_logistic_coefficients.csv", index=False)
        print("\nLogistic regression coefficients (top 10 by |coef|):")
        lr_coef["abs_coef"] = np.abs(lr_coef["coefficient"])
        print(lr_coef.nlargest(10, "abs_coef")[["feature", "coefficient"]].to_string(index=False))

        shap.summary_plot(shaps, X_shap, plot_type="bar", show=False, max_display=20)
        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / "classification_shap_bar.png", dpi=150, bbox_inches="tight")
        plt.close()
        print(f"Wrote {OUTPUT_DIR / 'classification_shap_bar.png'}")

        # SHAP beeswarm
        shap.summary_plot(shaps, X_shap, show=False, max_display=20)
        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / "classification_shap_beeswarm.png", dpi=150, bbox_inches="tight")
        plt.close()
        print(f"Wrote {OUTPUT_DIR / 'classification_shap_beeswarm.png'}")

    # Bar chart: one dimension example (e.g. operational_scope) success rate by value
    if "operational_scope" in ac.columns:
        op_scope = ac.groupby("operational_scope")["success_segment"].apply(
            lambda s: (s == "success").sum() / len(s) * 100
        ).sort_values(ascending=False).head(10)
        fig, ax = plt.subplots(figsize=(10, 4))
        op_scope.plot(kind="barh", ax=ax)
        ax.set_xlabel("Success rate (%)")
        ax.set_title("Success rate by operational_scope (classification cohort)")
        plt.tight_layout()
        fig.savefig(OUTPUT_DIR / "classification_operational_scope_success_rate.png", dpi=150, bbox_inches="tight")
        plt.close()
        print(f"Wrote {OUTPUT_DIR / 'classification_operational_scope_success_rate.png'}")


if __name__ == "__main__":
    main()
