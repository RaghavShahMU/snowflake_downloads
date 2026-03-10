#!/usr/bin/env python3
"""
Describe super_agent_run.csv: schema, row count, and per-column stats.
Run from repo root: python scripts/describe_super_agent_run.py
"""
import duckdb
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = REPO_ROOT / "data" / "super_agent_run.csv"


def main():
    path_str = str(CSV_PATH).replace("'", "''")
    con = duckdb.connect()

    con.execute(
        f"""
        CREATE OR REPLACE TEMP VIEW super_agent_run AS
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

    n = con.execute("SELECT count(*) FROM super_agent_run").fetchone()[0]
    print("=" * 60)
    print("SUPER_AGENT_RUN — Describe")
    print("=" * 60)
    print(f"Row count: {n:,}\n")

    schema = con.execute("DESCRIBE super_agent_run").fetchall()
    schema = [(r[0], r[1]) for r in schema]
    print("Schema (columns x type)")
    print("-" * 60)
    for col, dtype in schema:
        print(f"  {col}: {dtype}")
    print()

    print("Column stats (non_null, null, distinct) — first 25 columns")
    print("-" * 60)
    cols = [r[0] for r in schema]
    for col in cols[:25]:
        safe_col = f'"{col}"' if any(c in col for c in " ()") else col
        r = con.execute(
            f"SELECT count(*), count(*) - count({safe_col}), count(DISTINCT {safe_col}) FROM super_agent_run"
        ).fetchone()
        non_null, nulls, distinct = r[0] - r[1], r[1], r[2]
        print(f"  {col}: non_null={non_null:,}, null={nulls:,}, distinct={distinct:,}")
    print("  ... (remaining columns similar)")
    print()

    # Sample value counts for key dimensions
    for col in ["USE_TYPE", "TRIGGER_SOURCE", "EVENT_SURFACE", "ENTITLEMENT_NAME"]:
        if col not in cols:
            continue
        safe_col = f'"{col}"' if any(c in col for c in " ()") else col
        top = con.execute(
            f"SELECT {safe_col}, count(*) FROM super_agent_run GROUP BY {safe_col} ORDER BY 2 DESC LIMIT 5"
        ).fetchall()
        print(f"  {col} (top): {top}")
    print("=" * 60)


if __name__ == "__main__":
    main()
