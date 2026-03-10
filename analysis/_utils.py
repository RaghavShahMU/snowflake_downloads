"""Shared paths and DuckDB CSV loading for analysis scripts."""
from pathlib import Path
import duckdb

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
OUTPUT_DIR = REPO_ROOT / "analysis" / "output"


def get_connection():
    return duckdb.connect()


def _escape_path(p: Path) -> str:
    return str(p).replace("\\", "\\\\").replace("'", "''")


def load_csv_as_view(con: duckdb.DuckDBPyConnection, name: str, csv_path: Path) -> None:
    """Create a temp view from CSV with proper quote/escape for commas in cells."""
    path_str = _escape_path(csv_path)
    con.execute(
        f"""
        CREATE OR REPLACE TEMP VIEW {name} AS
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


def ensure_output_dir():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
