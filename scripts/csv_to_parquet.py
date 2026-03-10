#!/usr/bin/env python3
"""
Convert super_agent_run.csv to compressed Parquet using DuckDB.
Handles quoted fields (commas and special characters inside cells).
Run from repo root: python scripts/csv_to_parquet.py
"""
import duckdb
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
CSV_PATH = DATA_DIR / "super_agent_run.csv"
PARQUET_PATH = DATA_DIR / "super_agent_run.parquet"

def main():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV not found: {CSV_PATH}")

    print(f"Reading: {CSV_PATH}")
    print("(DuckDB will handle quoted fields and commas inside cells.)")

    def sql_escape(p: str) -> str:
        return p.replace("\\", "\\\\").replace("'", "''")

    con = duckdb.connect()
    csv_sql = sql_escape(str(CSV_PATH))
    parquet_sql = sql_escape(str(PARQUET_PATH))
    # read_csv: quote=" handles commas and special chars inside cells
    con.execute(
        f"""
        CREATE OR REPLACE TEMP VIEW run_data AS
        SELECT * FROM read_csv(
            '{csv_sql}',
            quote='"',
            escape='"',
            auto_detect=true,
            ignore_errors=false,
            maximum_line_size=2097152
        )
        """
    )
    con.execute(f"COPY run_data TO '{parquet_sql}' (FORMAT PARQUET, COMPRESSION zstd)")

    csv_size = CSV_PATH.stat().st_size / (1024**3)
    parquet_size = PARQUET_PATH.stat().st_size / (1024**3)
    print(f"Wrote: {PARQUET_PATH}")
    print(f"CSV size:     {csv_size:.2f} GB")
    print(f"Parquet size: {parquet_size:.2f} GB")
    print(f"Ratio:        {csv_size / parquet_size:.1f}x smaller")

if __name__ == "__main__":
    main()
