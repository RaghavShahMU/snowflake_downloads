#!/usr/bin/env python3
"""
Define success cohort: all agents in super_agents with segment success/failure/dormant/unknown.
Success = active and used after 7 days of creation. Failure = inactive or deleted. Dormant = active, no use post 7 days.
Output: cohort CSV + segment counts table + bar chart.
"""
import yaml
import duckdb
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

from _utils import REPO_ROOT, DATA_DIR, OUTPUT_DIR, get_connection, load_csv_as_view, ensure_output_dir


def load_config():
    with open(REPO_ROOT / "analysis" / "config.yaml") as f:
        return yaml.safe_load(f)


def main():
    ensure_output_dir()
    config = load_config()
    days_post = config["days_post_creation"]
    ref_date = config.get("analysis_reference_date")

    con = get_connection()
    load_csv_as_view(con, "super_agents", DATA_DIR / "super_agents.csv")
    load_csv_as_view(con, "super_agent_run", DATA_DIR / "super_agent_run.csv")

    # Use max run date as reference if not set
    if ref_date:
        ref_date_sql = f"DATE '{ref_date}'"
    else:
        ref_date_sql = "(SELECT max(CAST(RUN_STARTED_AT AS DATE)) FROM super_agent_run)"
        ref_date = con.execute("SELECT max(CAST(RUN_STARTED_AT AS DATE)) FROM super_agent_run").fetchone()[0]
        ref_date = str(ref_date) if ref_date else "unknown"

    # Per-agent: has at least one run after (AGENT_CREATED_AT + 7 days)
    con.execute(
        f"""
        CREATE OR REPLACE TEMP VIEW agent_usage_post_7d AS
        SELECT
            a.AGENT_ID,
            a.CURRENT_AGENT_STATUS,
            a.AGENT_CREATED_AT,
            a.AGENT_DELETED_AT,
            max(CASE WHEN r.RUN_STARTED_AT >= a.AGENT_CREATED_AT + INTERVAL '{days_post}' DAY THEN 1 ELSE 0 END) AS has_usage_after_7d
        FROM super_agents a
        LEFT JOIN super_agent_run r ON r.AGENT_ID = a.AGENT_ID
        GROUP BY a.AGENT_ID, a.CURRENT_AGENT_STATUS, a.AGENT_CREATED_AT, a.AGENT_DELETED_AT
        """
    )

    # Segment: failure first (inactive or deleted), then success (active + used after 7d), then dormant (active + not used after 7d), else unknown
    con.execute(
        """
        CREATE OR REPLACE TEMP VIEW cohort AS
        SELECT
            AGENT_ID,
            CURRENT_AGENT_STATUS,
            AGENT_CREATED_AT,
            AGENT_DELETED_AT,
            has_usage_after_7d,
            CASE
                WHEN CURRENT_AGENT_STATUS = 'deleted' OR CURRENT_AGENT_STATUS = 'inactive' OR AGENT_DELETED_AT IS NOT NULL
                THEN 'failure'
                WHEN CURRENT_AGENT_STATUS = 'active' AND has_usage_after_7d = 1
                THEN 'success'
                WHEN CURRENT_AGENT_STATUS = 'active' AND (has_usage_after_7d = 0 OR has_usage_after_7d IS NULL)
                THEN 'dormant'
                ELSE 'unknown'
            END AS success_segment
        FROM agent_usage_post_7d
        """
    )

    cohort_df = con.execute("SELECT * FROM cohort").fetchdf()
    cohort_df.to_csv(OUTPUT_DIR / "cohort.csv", index=False)
    print(f"Wrote {OUTPUT_DIR / 'cohort.csv'} ({len(cohort_df):,} rows)")

    # Segment counts
    counts = cohort_df["success_segment"].value_counts().sort_index()
    counts_df = counts.reset_index()
    counts_df.columns = ["segment", "agent_count"]
    counts_df.to_csv(OUTPUT_DIR / "cohort_segment_counts.csv", index=False)
    print("\nSegment counts:")
    print(counts_df.to_string(index=False))

    # Bar chart
    fig, ax = plt.subplots(figsize=(8, 4))
    segments = ["failure", "success", "dormant", "unknown"]
    vals = [counts.get(s, 0) for s in segments]
    colors = ["#e74c3c", "#2ecc71", "#f39c12", "#95a5a6"]
    ax.bar(segments, vals, color=colors)
    ax.set_ylabel("Agent count")
    ax.set_title("Success cohort distribution")
    for i, v in enumerate(vals):
        ax.text(i, v + max(vals) * 0.01, f"{v:,}", ha="center", fontsize=10)
    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "cohort_segment_distribution.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\nWrote {OUTPUT_DIR / 'cohort_segment_distribution.png'}")

    # Metadata for readout
    meta = {
        "analysis_reference_date": ref_date,
        "days_post_creation": days_post,
        "total_agents": int(len(cohort_df)),
        "segment_counts": counts.to_dict(),
    }
    with open(OUTPUT_DIR / "cohort_metadata.yaml", "w") as f:
        yaml.dump(meta, f, default_flow_style=False)
    print(f"Wrote {OUTPUT_DIR / 'cohort_metadata.yaml'}")


if __name__ == "__main__":
    main()
