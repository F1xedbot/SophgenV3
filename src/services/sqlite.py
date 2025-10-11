import sqlite3
from typing import Dict, Any, Optional, List

class SQLiteDBService:
    """
    Generic SQLite database handler.
    """

    def __init__(self, db_path: Optional[str] = None):
        from config.db import SQLITEConfig
        self.db_path = db_path or SQLITEConfig.get_db_path()
        self.table_sqls = SQLITEConfig.get_tables_sql()

    def init_db(self) -> None:
        """
        Initialize database and create tables.
        Accepts optional list of CREATE TABLE statements.
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        if self.table_sqls:
            for sql in self.table_sqls:
                c.execute(sql)
        conn.commit()
        conn.close()

    def save_data(
        self,
        table_name: str,
        data: Dict[str, Any]
    ) -> None:
        """
        Save a generic dict into the specified table.
        Keys -> column names, values -> column values.
        """
        if not data:
            raise ValueError("No data to insert")

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        values = list(data.values())

        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        c.execute(sql, values)

        conn.commit()
        conn.close()

    def get_data_group(
        self,
        table_name: str,
        group_key: str,
        group_value: Any
    ) -> List[Dict[str, Any]]:
        """
        Fetch all rows from `table_name` where `group_key` = `group_value`.
        Returns a list of dictionaries.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dict-like objects
        c = conn.cursor()

        sql = f"SELECT * FROM {table_name} WHERE {group_key} = ?"
        c.execute(sql, (group_value,))
        rows = c.fetchall()

        result = [dict(row) for row in rows]

        conn.close()
        return result
