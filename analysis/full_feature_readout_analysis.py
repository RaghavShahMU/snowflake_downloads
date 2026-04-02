#!/usr/bin/env python3
"""
Full-feature readout: one agent-level dataset with all features (prompts, triggers, templates, tools).
Runs distribution, population, RF, SHAP, SHAP beeswarm (by group), average SHAP per feature, logistic regression.
Exports all features (no cap). Correlation section: four matrices with annotated heatmaps.
Scope: classified agents only.
"""
import json
import duckdb
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import shap

from _utils import DATA_DIR, OUTPUT_DIR, get_connection, load_csv_as_view, ensure_output_dir

CLASS_DIMS = [
    "team_orientation", "domain_knowledge_depth", "operational_scope", "data_flow_direction",
    "autonomy_level", "functional_archetype", "tone_and_persona", "execution_dataset",
    "state_persistence", "external_integration_scope", "output_modality",
    "domain_industry_vertical", "use_case_context", "implied_end_date",
]

SHAP_SAMPLE_SIZE = 500
CELL_SIZE_INCH = 0.35  # for correlation heatmaps
DPI = 150
# Leadership readout: split tools into row/col blocks so heatmaps stay legible in the HTML explorer.
TOOL_GROUP_SIZE = 6
TOOL_GROUP_PREFIX = "tools_g"


def _split_tool_columns_into_groups(tool_cols, per_group=TOOL_GROUP_SIZE):
    cols = sorted(str(c) for c in tool_cols)
    if not cols:
        return []
    groups = []
    for i in range(0, len(cols), per_group):
        chunk = cols[i : i + per_group]
        groups.append((f"{TOOL_GROUP_PREFIX}{len(groups) + 1}", chunk))
    return groups


def _build_leadership_axis_map(class_cols, tool_cols, trigger_cols, template_cols, tool_group_size=TOOL_GROUP_SIZE):
    dim_ids = [d for d in CLASS_DIMS if any(str(c).startswith(d + "=") for c in class_cols)]
    axis_map = {}
    for d in dim_ids:
        axis_map[d] = [c for c in class_cols if str(c).startswith(d + "=")]
    tool_groups = _split_tool_columns_into_groups(tool_cols, per_group=tool_group_size)
    for gid, chunk in tool_groups:
        axis_map[gid] = chunk
    axis_map["triggers"] = list(trigger_cols)
    axis_map["templates"] = list(template_cols)
    return dim_ids, tool_groups, axis_map


def export_leadership_correlation_grid(
    corr_mat,
    class_cols,
    tool_cols,
    trigger_cols,
    template_cols,
    output_dir,
    dpi=150,
    tool_group_size=TOOL_GROUP_SIZE,
):
    """One heatmap per axis pair (dims, tools in ~6-column groups, triggers, templates); writes leadership_corr_heatmap_map.json."""
    dim_ids, tool_groups, axis_map = _build_leadership_axis_map(
        class_cols, tool_cols, trigger_cols, template_cols, tool_group_size=tool_group_size,
    )
    axis_ids = dim_ids + [g[0] for g in tool_groups] + ["triggers", "templates"]
    axis_ids = [a for a in axis_ids if axis_map.get(a)]

    tool_axis_options = [
        {"value": gid, "label": f"Tools group {i + 1}"}
        for i, (gid, chunk) in enumerate(tool_groups)
    ]
    (output_dir / "leadership_corr_tool_axis_options.json").write_text(
        json.dumps(tool_axis_options, indent=2),
        encoding="utf-8",
    )

    manifest = {}
    for rid in axis_ids:
        rcols = axis_map.get(rid) or []
        if not rcols:
            continue
        for cid in axis_ids:
            ccols = axis_map.get(cid) or []
            if not ccols:
                continue
            try:
                sub = corr_mat.loc[rcols, ccols]
            except (KeyError, ValueError):
                continue
            if sub.shape[0] == 0 or sub.shape[1] == 0:
                continue
            base = f"full_feature_corr_heatmap_rows_{rid}_cols_{cid}"
            png_path = output_dir / f"{base}.png"
            csv_path = output_dir / f"{base}.csv"
            sub.to_csv(csv_path)
            n_r, n_c = sub.shape
            use_annot = n_r * n_c <= 625
            annot_font = 5 if max(n_r, n_c) <= 28 else 4
            fig_w = max(6, min(48, n_c * CELL_SIZE_INCH * 0.55))
            fig_h = max(6, min(48, n_r * CELL_SIZE_INCH * 0.55))
            fig, ax = plt.subplots(figsize=(fig_w, fig_h))
            kw = dict(ax=ax, cmap="RdBu_r", center=0, vmin=-1, vmax=1, square=False)
            if use_annot:
                sns.heatmap(
                    sub, annot=True, fmt=".2f", annot_kws={"size": annot_font}, **kw,
                )
            else:
                sns.heatmap(sub, annot=False, **kw)
            ax.set_title(f"Rows: {rid} × Cols: {cid}")
            plt.xticks(rotation=90, ha="right", fontsize=max(3, annot_font - 1))
            plt.yticks(fontsize=max(3, annot_font - 1))
            plt.tight_layout()
            plt.savefig(png_path, dpi=dpi, bbox_inches="tight")
            plt.close()
            manifest[f"{rid}|{cid}"] = f"{base}.png"
    mp = output_dir / "leadership_corr_heatmap_map.json"
    mp.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print(
        f"Wrote {len(manifest)} leadership correlation slices, {mp.name}, "
        f"and leadership_corr_tool_axis_options.json ({len(tool_axis_options)} tool groups)",
    )


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
    load_csv_as_view(con, "super_agent_tools", DATA_DIR / "super_agent_tools.csv")

    # Classified cohort
    classified_agents = con.execute(
        "SELECT DISTINCT agent_id FROM agent_classifications"
    ).fetchdf()
    cohort_class = cohort_df[cohort_df["AGENT_ID"].isin(classified_agents["agent_id"])].copy()
    cohort_class = cohort_class.rename(columns={"AGENT_ID": "agent_id"})
    print(f"Classified agents in cohort: {len(cohort_class):,}")

    ac = pd.read_csv(DATA_DIR / "agent_classifications.csv")
    ac = ac.drop(columns=["business_items"], errors="ignore")
    ac = ac.merge(cohort_class[["agent_id", "success_segment"]], on="agent_id", how="inner")

    # One-hot classification dimensions
    onehot_list = []
    for col in CLASS_DIMS:
        if col not in ac.columns:
            continue
        dummies = pd.get_dummies(ac[col].fillna("unknown").astype(str), prefix=col, prefix_sep="=")
        onehot_list.append(dummies)
    X_class = pd.concat(onehot_list, axis=1)
    X_class = X_class.reindex(columns=sorted(X_class.columns), fill_value=0)
    class_cols = X_class.columns.tolist()

    # Primary trigger per agent
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
    ac["trigger_source"] = ac["trigger_source"].fillna("unknown").astype(str).str.strip()
    ac.loc[ac["trigger_source"] == "", "trigger_source"] = "unknown"
    trigger_dum = pd.get_dummies(ac["trigger_source"], prefix="trigger", prefix_sep="=")
    trigger_cols = trigger_dum.columns.tolist()

    # Primary template per agent
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
    ac["template_is_custom"] = (ac["TEMPLATE_TYPE"] == "custom").astype(int)
    ac["template_is_templated"] = (~ac["TEMPLATE_TYPE"].isin(["custom", "unknown"])).astype(int)
    template_dum = pd.get_dummies(ac["TEMPLATE_TYPE"], prefix="template", prefix_sep="=")
    template_extra = ac[["template_is_custom", "template_is_templated"]]
    template_cols = list(template_extra.columns) + template_dum.columns.tolist()

    # Tool usage per agent (avg per run)
    con.execute(
        """
        CREATE OR REPLACE TEMP VIEW clickup_tool_calls AS
        SELECT AGENT_ID, RUN_ID, CALL_NAME, 1 AS call_count
        FROM super_agent_tools
        WHERE CALL_TYPE = 'clickup_tool' AND TRIM(COALESCE(CALL_NAME, '')) != ''
        """
    )
    run_count = con.execute(
        """
        SELECT r.AGENT_ID, count(DISTINCT r.RUN_ID) AS run_count
        FROM super_agent_run r
        WHERE r.AGENT_ID IN (SELECT agent_id FROM agent_classifications)
        GROUP BY r.AGENT_ID
        """
    ).fetchdf()
    tool_totals = con.execute(
        """
        SELECT t.AGENT_ID, t.CALL_NAME, count(*) AS total_calls
        FROM (SELECT agent_id AS AGENT_ID FROM agent_classifications) c
        JOIN clickup_tool_calls t ON t.AGENT_ID = c.AGENT_ID
        GROUP BY t.AGENT_ID, t.CALL_NAME
        """
    ).fetchdf()
    tool_pivot = tool_totals.pivot_table(
        index="AGENT_ID", columns="CALL_NAME", values="total_calls", aggfunc="sum"
    ).fillna(0)
    agent_run = cohort_class[["agent_id", "success_segment"]].merge(
        run_count.rename(columns={"AGENT_ID": "agent_id"}), on="agent_id", how="left"
    )
    agent_run["run_count"] = agent_run["run_count"].fillna(0).clip(lower=1)
    wide_tools = agent_run.merge(
        tool_pivot.reset_index().rename(columns={"AGENT_ID": "agent_id"}),
        on="agent_id", how="left"
    ).fillna(0)
    tool_cols = [c for c in wide_tools.columns if c not in ("agent_id", "success_segment", "run_count")]
    for c in tool_cols:
        wide_tools[c] = wide_tools[c] / wide_tools["run_count"]

    # Full feature matrix: class | trigger | template_extra | template_dum | tools
    feature_cols = class_cols + trigger_cols + template_cols + tool_cols
    X_full = pd.concat([
        ac[["agent_id", "success_segment"]],
        X_class, trigger_dum, template_extra, template_dum
    ], axis=1)
    X_full = X_full.merge(wide_tools[["agent_id"] + tool_cols], on="agent_id", how="left").fillna(0)
    X_full = X_full.reindex(columns=["agent_id", "success_segment"] + feature_cols, fill_value=0)

    # --- Distribution ---
    # Trigger: value × segment + success_rate
    trigger_seg = ac.groupby("trigger_source")["success_segment"].value_counts().unstack(fill_value=0)
    trigger_seg["success_rate"] = trigger_seg.get("success", 0) / (trigger_seg.sum(axis=1) + 1e-9)
    trigger_seg.to_csv(OUTPUT_DIR / "full_feature_trigger_distribution.csv")
    # Template: value × segment + success_rate
    template_seg = ac.groupby("TEMPLATE_TYPE")["success_segment"].value_counts().unstack(fill_value=0)
    template_seg["success_rate"] = template_seg.get("success", 0) / (template_seg.sum(axis=1) + 1e-9)
    template_seg.to_csv(OUTPUT_DIR / "full_feature_template_distribution.csv")
    # Prompts: per-dimension (same as classification script)
    for col in CLASS_DIMS:
        if col not in ac.columns:
            continue
        tab = ac.groupby([col, "success_segment"]).size().unstack(fill_value=0)
        tab["success_rate"] = tab.get("success", 0) / (tab.sum(axis=1) + 1e-9)
        tab.to_csv(OUTPUT_DIR / f"classification_dim_{col}.csv")
    # Tools: segment × mean(avg_per_run) per tool
    tool_by_seg = X_full.groupby("success_segment")[tool_cols].mean().T
    tool_by_seg.to_csv(OUTPUT_DIR / "full_feature_tool_by_segment.csv")
    # Population
    pop = X_full["success_segment"].value_counts().to_frame("count")
    total = pop["count"].sum()
    overall_sr = pop.loc["success", "count"] / total if "success" in pop.index else 0
    pop["success_rate"] = overall_sr  # overall cohort success rate (same for all rows)
    pop.to_csv(OUTPUT_DIR / "full_feature_population.csv")
    print("Wrote distribution and population CSVs")

    # Optional agent table (no need to write if huge; plan says optional)
    # X_full.to_csv(OUTPUT_DIR / "full_feature_agent_table.csv", index=False)

    X = X_full[feature_cols].astype(float)
    y = (X_full["success_segment"] == "success").astype(int)
    if y.sum() < 10 or (1 - y).sum() < 10:
        print("Skipping RF/SHAP/LR: too few success or failure")
        return

    # --- Random forest ---
    model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    model.fit(X, y)
    importance = pd.DataFrame(
        {"feature": feature_cols, "importance": model.feature_importances_}
    ).sort_values("importance", ascending=False)
    importance.to_csv(OUTPUT_DIR / "full_feature_rf_importance.csv", index=False)
    n_f = len(feature_cols)
    fig, ax = plt.subplots(figsize=(12, max(8, n_f * 0.22)))
    y_pos = np.arange(n_f)
    ax.barh(y_pos, importance["importance"].values, align="center")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(importance["feature"].tolist(), fontsize=5)
    ax.invert_yaxis()
    ax.set_xlabel("Importance")
    ax.set_title("Full-feature RF importance (all features)")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "full_feature_rf_importance.png", dpi=DPI, bbox_inches="tight")
    plt.close()
    print("Wrote full_feature_rf_importance.csv and .png")

    # --- SHAP ---
    sample_size = min(SHAP_SAMPLE_SIZE, len(X))
    X_shap = X.sample(n=sample_size, random_state=42) if len(X) > sample_size else X.copy()
    explainer = shap.TreeExplainer(model, X_shap)
    shaps = explainer.shap_values(X_shap)
    if isinstance(shaps, list):
        shaps = shaps[1]
    if shaps.ndim == 3:
        shaps = shaps[:, :, 1]
    mean_abs = np.abs(shaps).mean(axis=0)
    mean_signed = shaps.mean(axis=0)
    shap_direction = pd.DataFrame({
        "feature": X_shap.columns.tolist(),
        "mean_shap": mean_signed,
        "mean_abs_shap": mean_abs,
    }).sort_values("mean_abs_shap", ascending=False)
    shap_direction.to_csv(OUTPUT_DIR / "full_feature_shap_direction.csv", index=False)

    # Average SHAP per feature: one-hot (0/1), continuous (quartiles)
    shap_by_value_rows = []
    for col in X_shap.columns:
        col_idx = list(X_shap.columns).index(col)
        if col in tool_cols:
            # Continuous: quartiles
            q = X_shap[col].quantile([0.25, 0.5, 0.75]).values
            for i, (lo, hi) in enumerate([(None, q[0]), (q[0], q[1]), (q[1], q[2]), (q[2], None)]):
                mask = np.ones(len(X_shap), dtype=bool)
                if lo is not None:
                    mask &= X_shap[col].values >= lo
                if hi is not None:
                    mask &= X_shap[col].values <= hi
                if mask.sum() == 0:
                    continue
                shap_by_value_rows.append({
                    "feature": col,
                    "value": f"q{i+1}",
                    "mean_shap": float(shaps[mask, col_idx].mean()),
                    "n_agents": int(mask.sum()),
                })
        else:
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
    pd.DataFrame(shap_by_value_rows).to_csv(OUTPUT_DIR / "full_feature_shap_by_value.csv", index=False)

    # SHAP beeswarm: split by feature group for readability
    for group_name, cols in [
        ("prompts", class_cols),
        ("triggers", trigger_cols),
        ("templates", template_cols),
        ("tools", tool_cols),
    ]:
        cols_in = [c for c in cols if c in X_shap.columns]
        if not cols_in:
            continue
        idx = [X_shap.columns.get_loc(c) for c in cols_in]
        shaps_sub = shaps[:, idx]
        X_sub = X_shap[cols_in]
        shap.summary_plot(shaps_sub, X_sub, show=False, max_display=len(cols_in))
        fig = plt.gcf()
        fig.set_size_inches(10, max(4, len(cols_in) * 0.25))
        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / f"full_feature_shap_beeswarm_{group_name}.png", dpi=DPI, bbox_inches="tight")
        plt.close()
    print("Wrote full_feature_shap_direction.csv, full_feature_shap_by_value.csv, beeswarm_*.png")

    # --- Logistic regression ---
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    lr = LogisticRegression(C=1e6, max_iter=2000, random_state=42)
    lr.fit(X_scaled, y)
    lr_coef = pd.DataFrame({"feature": feature_cols, "coefficient": lr.coef_[0]})
    lr_coef.to_csv(OUTPUT_DIR / "full_feature_logistic_coefficients.csv", index=False)
    fig, ax = plt.subplots(figsize=(12, max(8, n_f * 0.22)))
    coef_sorted = lr_coef.reindex(importance["feature"].tolist()).dropna()
    y_pos = np.arange(len(coef_sorted))
    ax.barh(y_pos, coef_sorted["coefficient"].values, align="center")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(coef_sorted["feature"].tolist(), fontsize=5)
    ax.invert_yaxis()
    ax.axvline(0, color="gray", linewidth=0.5)
    ax.set_xlabel("Coefficient")
    ax.set_title("Full-feature logistic regression coefficients")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "full_feature_logistic_coefficients.png", dpi=DPI, bbox_inches="tight")
    plt.close()
    print("Wrote full_feature_logistic_coefficients.csv and .png")

    # --- Correlation matrices (all values) + heatmaps ---
    all_cols = class_cols + trigger_cols + template_cols + tool_cols
    data = X_full[all_cols].astype(float)
    corr_mat = data.corr()

    def save_heatmap(corr_sub, path_csv, path_png, title, annot_font=6):
        corr_sub.to_csv(path_csv)
        n_r, n_c = corr_sub.shape
        if n_r == 0 or n_c == 0:
            return
        fig_w = max(6, n_c * CELL_SIZE_INCH)
        fig_h = max(6, n_r * CELL_SIZE_INCH)
        fig, ax = plt.subplots(figsize=(fig_w, fig_h))
        sns.heatmap(
            corr_sub, ax=ax, annot=True, fmt=".2f", cmap="RdBu_r", center=0,
            vmin=-1, vmax=1, annot_kws={"size": annot_font}, square=False,
        )
        ax.set_title(title)
        plt.xticks(rotation=90, ha="right", fontsize=annot_font)
        plt.yticks(fontsize=annot_font)
        plt.tight_layout()
        plt.savefig(path_png, dpi=DPI, bbox_inches="tight")
        plt.close()

    # Prompts vs Prompts (large: reduce annot or size)
    corr_pp = corr_mat.loc[class_cols, class_cols]
    corr_pp.to_csv(OUTPUT_DIR / "full_feature_corr_prompts_vs_prompts.csv")
    n_pp = len(class_cols)
    fig_pp = max(20, n_pp * CELL_SIZE_INCH * 0.5)  # slightly smaller cells for 80x80
    fig, ax = plt.subplots(figsize=(fig_pp, fig_pp))
    sns.heatmap(corr_pp, ax=ax, annot=False, cmap="RdBu_r", center=0, vmin=-1, vmax=1, square=True)
    ax.set_title("Prompts vs Prompts (correlation); values in full_feature_corr_prompts_vs_prompts.csv")
    plt.xticks(rotation=90, ha="right", fontsize=4)
    plt.yticks(fontsize=4)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "full_feature_corr_heatmap_prompts_vs_prompts.png", dpi=DPI, bbox_inches="tight")
    plt.close()
    # With values: do a smaller annotated version (e.g. first 30x30) or annot with tiny font
    fig2, ax2 = plt.subplots(figsize=(fig_pp, fig_pp))
    sns.heatmap(corr_pp, ax=ax2, annot=True, fmt=".1f", cmap="RdBu_r", center=0, vmin=-1, vmax=1,
                annot_kws={"size": 3}, square=True)
    ax2.set_title("Prompts vs Prompts (values in cells)")
    plt.xticks(rotation=90, ha="right", fontsize=4)
    plt.yticks(fontsize=4)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "full_feature_corr_heatmap_prompts_vs_prompts_annot.png", dpi=200, bbox_inches="tight")
    plt.close()

    # Prompts vs Tools
    corr_pt = corr_mat.loc[class_cols, tool_cols]
    save_heatmap(
        corr_pt,
        OUTPUT_DIR / "full_feature_corr_prompts_vs_tools.csv",
        OUTPUT_DIR / "full_feature_corr_heatmap_prompts_vs_tools.png",
        "Prompts vs Tools",
        annot_font=5,
    )

    # Prompts vs Triggers
    corr_ptr = corr_mat.loc[class_cols, trigger_cols]
    save_heatmap(
        corr_ptr,
        OUTPUT_DIR / "full_feature_corr_prompts_vs_triggers.csv",
        OUTPUT_DIR / "full_feature_corr_heatmap_prompts_vs_triggers.png",
        "Prompts vs Triggers",
    )

    # Prompts vs Templates
    corr_ptm = corr_mat.loc[class_cols, template_cols]
    save_heatmap(
        corr_ptm,
        OUTPUT_DIR / "full_feature_corr_prompts_vs_templates.csv",
        OUTPUT_DIR / "full_feature_corr_heatmap_prompts_vs_templates.png",
        "Prompts vs Templates",
    )

    # Leadership readout matrix explorer: transposes and variable blocks
    save_heatmap(
        corr_pt.T,
        OUTPUT_DIR / "full_feature_corr_tools_vs_prompts.csv",
        OUTPUT_DIR / "full_feature_corr_heatmap_tools_vs_prompts.png",
        "Tools vs Prompts",
        annot_font=5,
    )
    save_heatmap(
        corr_ptr.T,
        OUTPUT_DIR / "full_feature_corr_triggers_vs_prompts.csv",
        OUTPUT_DIR / "full_feature_corr_heatmap_triggers_vs_prompts.png",
        "Triggers vs Prompts",
    )
    save_heatmap(
        corr_ptm.T,
        OUTPUT_DIR / "full_feature_corr_templates_vs_prompts.csv",
        OUTPUT_DIR / "full_feature_corr_heatmap_templates_vs_prompts.png",
        "Templates vs Prompts",
    )
    if len(tool_cols) > 0:
        corr_tt = corr_mat.loc[tool_cols, tool_cols]
        save_heatmap(
            corr_tt,
            OUTPUT_DIR / "full_feature_corr_tools_vs_tools.csv",
            OUTPUT_DIR / "full_feature_corr_heatmap_tools_vs_tools.png",
            "Tools vs Tools",
            annot_font=4,
        )
    if len(trigger_cols) > 0:
        corr_trtr = corr_mat.loc[trigger_cols, trigger_cols]
        save_heatmap(
            corr_trtr,
            OUTPUT_DIR / "full_feature_corr_triggers_vs_triggers.csv",
            OUTPUT_DIR / "full_feature_corr_heatmap_triggers_vs_triggers.png",
            "Triggers vs Triggers",
        )
    if len(template_cols) > 0:
        corr_tm = corr_mat.loc[template_cols, template_cols]
        save_heatmap(
            corr_tm,
            OUTPUT_DIR / "full_feature_corr_templates_vs_templates.csv",
            OUTPUT_DIR / "full_feature_corr_heatmap_templates_vs_templates.png",
            "Templates vs Templates",
        )
    if len(tool_cols) > 0 and len(trigger_cols) > 0:
        corr_ttr = corr_mat.loc[tool_cols, trigger_cols]
        save_heatmap(
            corr_ttr,
            OUTPUT_DIR / "full_feature_corr_tools_vs_triggers.csv",
            OUTPUT_DIR / "full_feature_corr_heatmap_tools_vs_triggers.png",
            "Tools vs Triggers",
        )
        save_heatmap(
            corr_ttr.T,
            OUTPUT_DIR / "full_feature_corr_triggers_vs_tools.csv",
            OUTPUT_DIR / "full_feature_corr_heatmap_triggers_vs_tools.png",
            "Triggers vs Tools",
        )
    if len(tool_cols) > 0 and len(template_cols) > 0:
        corr_ttm = corr_mat.loc[tool_cols, template_cols]
        save_heatmap(
            corr_ttm,
            OUTPUT_DIR / "full_feature_corr_tools_vs_templates.csv",
            OUTPUT_DIR / "full_feature_corr_heatmap_tools_vs_templates.png",
            "Tools vs Templates",
        )
        save_heatmap(
            corr_ttm.T,
            OUTPUT_DIR / "full_feature_corr_templates_vs_tools.csv",
            OUTPUT_DIR / "full_feature_corr_heatmap_templates_vs_tools.png",
            "Templates vs Tools",
        )
    if len(trigger_cols) > 0 and len(template_cols) > 0:
        corr_trtm = corr_mat.loc[trigger_cols, template_cols]
        save_heatmap(
            corr_trtm,
            OUTPUT_DIR / "full_feature_corr_triggers_vs_templates.csv",
            OUTPUT_DIR / "full_feature_corr_heatmap_triggers_vs_templates.png",
            "Triggers vs Templates",
        )
        save_heatmap(
            corr_trtm.T,
            OUTPUT_DIR / "full_feature_corr_templates_vs_triggers.csv",
            OUTPUT_DIR / "full_feature_corr_heatmap_templates_vs_triggers.png",
            "Templates vs Triggers",
        )

    export_leadership_correlation_grid(
        corr_mat, class_cols, tool_cols, trigger_cols, template_cols, OUTPUT_DIR, dpi=DPI,
    )

    print("Wrote correlation matrices and heatmaps")
    print("Done.")


if __name__ == "__main__":
    main()
