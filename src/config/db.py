from pathlib import Path
import os
from helpers.pydantic_to_sql import pydantic_model_to_create_table_sql
from schema.agents import InjectionSchema, ValidationSchema
from utils.enum import AgentTable

class SQLITEConfig:
    """
    SQLite database configuration.
    """
    PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT", ".")).resolve()
    DB_PATH = (PROJECT_ROOT / os.getenv("SQLITE3_PATH", "data/sophgen.db")).resolve()

    EXTRA_COLUMNS = [("func_name", "TEXT", True)]

    INJECTIONS_SQL = pydantic_model_to_create_table_sql(
        InjectionSchema,
        table_name=AgentTable.INJECTOR,
        extra_columns=EXTRA_COLUMNS,
        add_id_pk=True,
        add_timestamp=True
    )

    VALIDATIONS_SQL = pydantic_model_to_create_table_sql(
        ValidationSchema,
        table_name=AgentTable.VALIDATOR,
        extra_columns=EXTRA_COLUMNS,
        add_id_pk=True,
        add_timestamp=True
    )

    TABLES_SQL = [INJECTIONS_SQL, VALIDATIONS_SQL]

    @classmethod
    def get_db_path(cls) -> str:
        """Return the SQLite DB path and ensure parent folder exists."""
        cls.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        return str(cls.DB_PATH)

    @classmethod
    def get_tables_sql(cls) -> list[str]:
        """Return the list of table creation SQL strings."""
        return cls.TABLES_SQL