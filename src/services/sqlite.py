import aiosqlite
from typing import Dict, Any, Optional, List, Iterable
import os

class SQLiteDBService:
    """
    Generic SQLite database handler without a shared async connection.
    """

    def __init__(self, db_path: Optional[str] = None):
        from config.db import SQLITEConfig
        self.db_path = os.path.abspath(db_path or SQLITEConfig.get_db_path())
        self.table_sqls = SQLITEConfig.get_tables_sql()

    async def init_db(self) -> None:
        """Initialize database and create tables."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute("PRAGMA synchronous = NORMAL;")
            if self.table_sqls:
                for sql in self.table_sqls:
                    await db.execute(sql)
            await db.commit()

    async def save_data(self, table_name: str, data: Dict[str, Any]) -> None:
        """Insert a dict into a table."""
        if not data:
            raise ValueError("No data to insert")

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute("PRAGMA synchronous = NORMAL;")
            db.row_factory = aiosqlite.Row

            columns = ", ".join(data.keys())
            placeholders = ", ".join(["?"] * len(data))
            values = list(data.values())
            sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
            await db.execute(sql, values)
            await db.commit()

    async def get_data_group(
        self, table_name: str, group_key: str | None = None, group_value: Any = None
    ) -> List[Dict[str, Any]]:
        """Fetch rows optionally filtered by group_key = group_value."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute("PRAGMA synchronous = NORMAL;")
            db.row_factory = aiosqlite.Row

            if group_key is None or group_value is None:
                sql = f"SELECT * FROM {table_name}"
                async with db.execute(sql) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]

            sql = f"SELECT * FROM {table_name} WHERE {group_key} = ?"
            async with db.execute(sql, (group_value,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_data_by_keys(
        self, table_name: str, key_field: str, keys: Iterable[Any]
    ) -> List[Dict[str, Any]]:
        """Fetch rows where key_field is in the provided set of keys."""
        keys_list = list(keys)
        if not keys_list:
            return []

        placeholders = ", ".join(["?"] * len(keys_list))
        sql = f"SELECT * FROM {table_name} WHERE {key_field} IN ({placeholders})"

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute("PRAGMA synchronous = NORMAL;")
            db.row_factory = aiosqlite.Row

            async with db.execute(sql, keys_list) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
