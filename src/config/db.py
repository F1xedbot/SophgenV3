from pathlib import Path
import os
from helpers.pydantic_to_sql import pydantic_model_to_create_table_sql
from schema.agents import InjectionSchema

class SQLITEConfig:
    """
    SQLite database configuration.
    """
    PROJECT_ROOT: Path = Path(os.getenv("PROJECT_ROOT", Path.cwd()))
    DB_PATH: Path = PROJECT_ROOT / os.getenv("SQLITE3_PATH", "data/sophgen.db")

    EXTRA_COLUMNS = [("func_name", "TEXT", True)]

    INJECTIONS_SQL = pydantic_model_to_create_table_sql(
        InjectionSchema,
        table_name="injections",
        extra_columns=EXTRA_COLUMNS,
        add_id_pk=True,
        add_timestamp=True
    )

    TABLES_SQL = [INJECTIONS_SQL]

    @classmethod
    def get_db_path(cls) -> str:
        """Return the SQLite DB path and ensure parent folder exists."""
        cls.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        return str(cls.DB_PATH)

    @classmethod
    def get_tables_sql(cls) -> list[str]:
        """Return the list of table creation SQL strings."""
        return cls.TABLES_SQL