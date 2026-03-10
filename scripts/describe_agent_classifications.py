#!/usr/bin/env python3
"""
Describe agent_classifications.csv: schema and distinct values per column.
Grain: one row per agent (LLM-classified from agent/memory prompt). Join to super_agents on agent_id.
Run from repo root: python scripts/describe_agent_classifications.py
"""
import duckdb
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = REPO_ROOT / "data" / "agent_classifications.csv"


def main():
    path_str = str(CSV_PATH).replace("'", "''")
    con = duckdb.connect()
    con.execute(
        f"""
        CREATE OR REPLACE TEMP VIEW agent_classifications AS
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
    n = con.execute("SELECT count(*) FROM agent_classifications").fetchone()[0]
    print("=" * 60)
    print("AGENT_CLASSIFICATIONS — Describe")
    print("=" * 60)
    print(f"Row count: {n:,}\n")
    schema = con.execute("DESCRIBE agent_classifications").fetchall()
    cols = [r[0] for r in schema]
    print("Distinct values per column (classification dimensions)")
    print("-" * 60)
    for col in cols:
        safe = f'"{col}"' if " " in col else col
        vals = con.execute(
            f"SELECT {safe}, count(*) FROM agent_classifications GROUP BY {safe} ORDER BY 2 DESC"
        ).fetchall()
        print(f"\n  {col} ({len(vals)} distinct):")
        for v, c in vals[:15]:
            disp = (str(v)[:60] + "..") if v and len(str(v)) > 60 else v
            print(f"    {disp!r} -> {c:,}")
        if len(vals) > 15:
            print(f"    ... and {len(vals) - 15} more")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
