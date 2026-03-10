#!/usr/bin/env python3
"""
Describe super_agent_tools.csv: schema, row count, and key column stats.
Grain: one row per tool call. Join to super_agents (AGENT_ID), super_agent_run (RUN_ID).
Run from repo root: python scripts/describe_super_agent_tools.py
"""
import duckdb
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = REPO_ROOT / "data" / "super_agent_tools.csv"


def main():
    path_str = str(CSV_PATH).replace("'", "''")
    con = duckdb.connect()

    # Use sample for schema if file is huge; full scan for count can be slow
    con.execute(
        f"""
        CREATE OR REPLACE TEMP VIEW super_agent_tools AS
        SELECT * FROM read_csv(
            '{path_str}',
            quote='"',
            escape='"',
            auto_detect=true,
            ignore_errors=false,
            maximum_line_size=2097152
        )
        """
    )

    n = con.execute("SELECT count(*) FROM super_agent_tools").fetchone()[0]
    print("=" * 60)
    print("SUPER_AGENT_TOOLS — Describe")
    print("=" * 60)
    print(f"Row count: {n:,}\n")

    schema = con.execute("DESCRIBE super_agent_tools").fetchall()
    schema = [(r[0], r[1]) for r in schema]
    print("Schema (columns x type)")
    print("-" * 60)
    for col, dtype in schema:
        print(f"  {col}: {dtype}")
    print()

    # Key dimensions: distinct run_id, agent_id
    r = con.execute(
        "SELECT count(DISTINCT RUN_ID), count(DISTINCT AGENT_ID) FROM super_agent_tools"
    ).fetchone()
    print(f"Distinct RUN_ID: {r[0]:,}  |  Distinct AGENT_ID: {r[1]:,}\n")

    # Sample value counts for CALL_TYPE, CALL_SUBTYPE
    for col in ["CALL_TYPE", "CALL_SUBTYPE", "VENDOR"]:
        if not any(r[0] == col for r in schema):
            continue
        safe = f'"{col}"' if " " in col else col
        top = con.execute(
            f"SELECT {safe}, count(*) FROM super_agent_tools GROUP BY {safe} ORDER BY 2 DESC LIMIT 8"
        ).fetchall()
        print(f"  {col} (top): {top}")
    print("=" * 60)


if __name__ == "__main__":
    main()
