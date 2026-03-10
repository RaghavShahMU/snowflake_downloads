#!/usr/bin/env python3
"""
Describe super_agents.csv: schema, row count, and per-column stats.
Run from repo root: python scripts/describe_super_agents.py
"""
import duckdb
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = REPO_ROOT / "data" / "super_agents.csv"


def main():
    path_str = str(CSV_PATH).replace("'", "''")
    con = duckdb.connect()

    # Load with proper CSV quoting (commas/special chars in cells)
    con.execute(
        f"""
        CREATE OR REPLACE TEMP VIEW super_agents AS
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

    # Row count
    n = con.execute("SELECT count(*) FROM super_agents").fetchone()[0]
    print("=" * 60)
    print("SUPER_AGENTS — Describe")
    print("=" * 60)
    print(f"Row count: {n:,}\n")

    # Schema (column name, type)
    schema = con.execute("DESCRIBE super_agents").fetchall()
    # DESCRIBE returns column_name, column_type, null, key, default, extra
    schema = [(r[0], r[1]) for r in schema]
    print("Schema (columns × type)")
    print("-" * 60)
    for col, dtype in schema:
        print(f"  {col}: {dtype}")
    print()

    # Per-column: non-null, null, distinct, and sample/summary
    cols = [r[0] for r in schema]
    print("Column stats (non_null, null, distinct)")
    print("-" * 60)
    for col in cols:
        safe_col = f'"{col}"' if any(c in col for c in " ()") else col
        r = con.execute(
            f"""
            SELECT
                count(*) AS n,
                count(*) - count({safe_col}) AS nulls,
                count(DISTINCT {safe_col}) AS distinct_count
            FROM super_agents
            """
        ).fetchone()
        non_null = r[0] - r[1]
        nulls = r[1]
        distinct = r[2]
        print(f"  {col}")
        print(f"    non_null={non_null:,}, null={nulls:,}, distinct={distinct:,}")
    print()

    # Numeric columns: min, max, mean (for a few key ones if any)
    numeric_cols = [
        r[0]
        for r in schema
        if r[1] in ("BIGINT", "DOUBLE", "INTEGER", "HUGEINT")
    ]
    if numeric_cols:
        print("Numeric columns — min, max, mean (sample)")
        print("-" * 60)
        for col in numeric_cols[:15]:  # first 15 to avoid huge output
            safe_col = f'"{col}"' if any(c in col for c in " ()") else col
            try:
                stats = con.execute(
                    f"""
                    SELECT min({safe_col}), max({safe_col}), avg({safe_col})
                    FROM super_agents
                    """
                ).fetchone()
                if stats[0] is not None:
                    print(f"  {col}: min={stats[0]}, max={stats[1]}, mean={stats[2]:.4f}")
            except Exception as e:
                print(f"  {col}: (skip) {e}")
    print()

    # Sample values for a few important string/enum-like columns
    sample_cols = [
        "AGENT_CLASSIFICATION",
        "CURRENT_AGENT_STATUS",
        "AGENT_VERSION",
        "METADATA_SHARD",
    ]
    sample_cols = [c for c in sample_cols if c in cols]
    print("Sample value counts (top 5) for selected columns")
    print("-" * 60)
    for col in sample_cols:
        safe_col = f'"{col}"' if any(c in col for c in " ()") else col
        top = con.execute(
            f"""
            SELECT {safe_col} AS v, count(*) AS c
            FROM super_agents
            GROUP BY {safe_col}
            ORDER BY c DESC
            LIMIT 5
            """
        ).fetchall()
        print(f"  {col}:")
        for v, c in top:
            disp = str(v)[:50] + "..." if v and len(str(v)) > 50 else v
            print(f"    {disp!r} -> {c:,}")
    print("=" * 60)


if __name__ == "__main__":
    main()
