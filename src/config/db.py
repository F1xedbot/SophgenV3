from pathlib import Path
import os
from helpers.pydantic_to_sql import pydantic_model_to_create_table_sql
from schema.agents import InjectionSchema, ValidationSchema, ResearcherSchema, CondenserSchema
from schema.base import FunctionMetadataSchema, FunctionRawSchema
from utils.enums import AgentTable

class SQLITEConfig:
    """
    SQLite database configuration.
    """
    PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT", ".")).resolve()
    DB_PATH = (PROJECT_ROOT / os.getenv("SQLITE3_PATH", "data/sophgen.db")).resolve()
    
    EXTRA_INJECTOR_COLUMNS = [("func_name", "TEXT", True), ("lines", "TEXT", True), ("ref_hash", "TEXT", True)]
    EXTRA_VALIDATOR_COLUMNS = [("func_name", "TEXT", True), ("lines", "TEXT", True)]

    FUNCTION_RAW_SQL = pydantic_model_to_create_table_sql(
        FunctionRawSchema,
        table_name="functions",
        add_id_pk=True,
        add_timestamp=False
    )

    FUNCTION_METADATA_SQL = pydantic_model_to_create_table_sql(
        FunctionMetadataSchema,
        table_name="functions_metadata",
        add_id_pk=True,
        add_timestamp=False
    )

    INJECTIONS_SQL = pydantic_model_to_create_table_sql(
        InjectionSchema,
        table_name=AgentTable.INJECTOR,
        extra_columns=EXTRA_INJECTOR_COLUMNS,
        add_id_pk=True,
        add_timestamp=True
    )

    VALIDATIONS_SQL = pydantic_model_to_create_table_sql(
        ValidationSchema,
        table_name=AgentTable.VALIDATOR,
        extra_columns=EXTRA_VALIDATOR_COLUMNS,
        add_id_pk=True,
        add_timestamp=True
    )

    RESEARCHER_SQL = pydantic_model_to_create_table_sql(
        ResearcherSchema,
        table_name=AgentTable.RESEARCHER,
        add_id_pk=True,
        add_timestamp=True,
    )

    CONDENSER_SQL = pydantic_model_to_create_table_sql(
        CondenserSchema,
        table_name=AgentTable.CONDENSER,
        add_id_pk=True,
        add_timestamp=True
    )

    TABLES_SQL = [FUNCTION_RAW_SQL, FUNCTION_METADATA_SQL, INJECTIONS_SQL, VALIDATIONS_SQL, RESEARCHER_SQL, CONDENSER_SQL]

    @classmethod
    def get_db_path(cls) -> str:
        """Return the SQLite DB path and ensure parent folder exists."""
        cls.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        return str(cls.DB_PATH)

    @classmethod
    def get_tables_sql(cls) -> list[str]:
        """Return the list of table creation SQL strings."""
        return cls.TABLES_SQL