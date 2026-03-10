#!/usr/bin/env python3
"""
Prompts readout: agent-level dataset (classified agents + trigger + template + tool usage)
and per-dimension correlation with tools/triggers/templates for the prompts-only classification readout.
Outputs: prompts_readout_correlation_<dim>.csv per dimension (top 5-10 positive and negative).
"""
import duckdb
import pandas as pd
import numpy as np
from pathlib import Path

from _utils import REPO_ROOT, DATA_DIR, OUTPUT_DIR, get_connection, load_csv_as_view, ensure_output_dir

CLASS_DIMS = [
    "team_orientation", "domain_knowledge_depth", "operational_scope", "data_flow_direction",
    "autonomy_level", "functional_archetype", "tone_and_persona", "execution_dataset",
    "state_persistence", "external_integration_scope", "output_modality",
    "domain_industry_vertical", "use_case_context", "implied_end_date",
]

TOP_N_CORR = 10  # top N positive and top N negative per dimension


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

    ac = pd.read_csv(DATA_DIR / "agent_classifications.csv")
    ac = ac.drop(columns=["business_items"], errors="ignore")
    ac = ac.merge(cohort_class[["agent_id", "success_segment"]], on="agent_id", how="inner")

    # Primary trigger per agent (classified only)
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

    # Tool usage per agent (classified only): run_count and tool totals
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

    # One-hot: classification, trigger, template
    onehot_list = []
    for col in CLASS_DIMS:
        if col not in ac.columns:
            continue
        dummies = pd.get_dummies(ac[col].fillna("unknown").astype(str), prefix=col, prefix_sep="=")
        onehot_list.append(dummies)
    X_class = pd.concat(onehot_list, axis=1)
    X_class = X_class.reindex(columns=sorted(X_class.columns), fill_value=0)

    trigger_dum = pd.get_dummies(ac["trigger_source"], prefix="trigger", prefix_sep="=")
    template_dum = pd.get_dummies(ac["TEMPLATE_TYPE"], prefix="template", prefix_sep="=")

    # Merge: ac (agent_id, success_segment) + X_class + trigger_dum + template_dum + tool cols
    agent_df = pd.concat([ac[["agent_id", "success_segment"]], X_class, trigger_dum, template_dum], axis=1)
    agent_df = agent_df.merge(
        wide_tools[["agent_id"] + tool_cols], on="agent_id", how="left"
    ).fillna(0)

    class_cols = X_class.columns.tolist()
    external_cols = list(trigger_dum.columns) + list(template_dum.columns) + tool_cols

    # Correlation: classification one-hots vs external (trigger, template, tool)
    corr_mat = agent_df[class_cols + external_cols].astype(float).corr()
    # We want class_cols (rows) vs external_cols (columns)
    corr_sub = corr_mat.loc[class_cols, external_cols]

    # Per dimension: top TOP_N_CORR positive and top TOP_N_CORR negative
    for dim in CLASS_DIMS:
        prefix = dim + "="
        dim_cols = [c for c in class_cols if c.startswith(prefix)]
        if not dim_cols:
            continue
        rows = []
        for feat in dim_cols:
            for ext in external_cols:
                r = corr_sub.loc[feat, ext]
                if np.isfinite(r):
                    rows.append({"classification_feature": feat, "external_feature": ext, "correlation": r})
        if not rows:
            continue
        df = pd.DataFrame(rows).sort_values("correlation", ascending=False)
        pos = df[df["correlation"] > 0].head(TOP_N_CORR)
        neg = df[df["correlation"] < 0].tail(TOP_N_CORR).sort_values("correlation", ascending=True)
        out = pd.concat([pos, neg], ignore_index=True)
        out.to_csv(OUTPUT_DIR / f"prompts_readout_correlation_{dim}.csv", index=False)

    # Optional: combined top-by-dimension (one row per dim with top positive/negative)
    combined = []
    for dim in CLASS_DIMS:
        p = OUTPUT_DIR / f"prompts_readout_correlation_{dim}.csv"
        if p.exists():
            df = pd.read_csv(p)
            df.insert(0, "dimension", dim)
            combined.append(df)
    if combined:
        pd.concat(combined, ignore_index=True).to_csv(
            OUTPUT_DIR / "prompts_readout_correlation_top_by_dimension.csv", index=False
        )

    print(f"Wrote prompts_readout_correlation_<dim>.csv for {len(CLASS_DIMS)} dimensions")
    print(f"Wrote prompts_readout_correlation_top_by_dimension.csv")


if __name__ == "__main__":
    main()
