import aiosqlite
from typing import Dict, Any, Optional, List
import os

class SQLiteDBService:
    """
    Generic SQLite database handler with a shared async connection.
    """

    def __init__(self, db_path: Optional[str] = None):
        from config.db import SQLITEConfig
        self.db_path = os.path.abspath(db_path or SQLITEConfig.get_db_path())
        self.table_sqls = SQLITEConfig.get_tables_sql()
        self.db: Optional[aiosqlite.Connection] = None  # shared connection

    async def connect(self):
        """Ensure a persistent aiosqlite connection is established."""
        if self.db is None:
            self.db = await aiosqlite.connect(self.db_path)
            await self.db.execute("PRAGMA journal_mode=WAL;")
            await self.db.execute("PRAGMA synchronous = NORMAL;")
            self.db.row_factory = aiosqlite.Row
            await self.db.commit()

    async def close(self):
        """Gracefully close the database connection."""
        if self.db:
            await self.db.close()
            self.db = None

    async def init_db(self) -> None:
        """Initialize database and create tables."""
        await self.connect()
        if self.table_sqls:
            for sql in self.table_sqls:
                await self.db.execute(sql)
        await self.db.commit()

    async def save_data(self, table_name: str, data: Dict[str, Any]) -> None:
        """Insert a dict into a table (non-blocking shared connection)."""
        if not data:
            raise ValueError("No data to insert")

        await self.connect()

        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        values = list(data.values())
        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

        await self.db.execute(sql, values)
        await self.db.commit()

    async def get_data_group(
        self, table_name: str, group_key: str, group_value: Any
    ) -> List[Dict[str, Any]]:
        """Fetch rows where group_key = group_value using shared connection."""
        await self.connect()
        sql = f"SELECT * FROM {table_name} WHERE {group_key} = ?"
        async with self.db.execute(sql, (group_value,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]