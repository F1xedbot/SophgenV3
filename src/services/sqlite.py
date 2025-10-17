import aiosqlite
from typing import Dict, Any, Optional, List

class SQLiteDBService:
    """
    Generic SQLite database handler.
    """

    def __init__(self, db_path: Optional[str] = None):
        from config.db import SQLITEConfig
        self.db_path = db_path or SQLITEConfig.get_db_path()
        self.table_sqls = SQLITEConfig.get_tables_sql()

    async def init_db(self) -> None:
        """
        Initialize database and create tables.
        Accepts optional list of CREATE TABLE statements.
        """
        async with aiosqlite.connect(self.db_path) as db:
            if self.table_sqls:
                for sql in self.table_sqls:
                    await db.execute(sql)
            await db.commit()

    async def save_data(self, table_name: str, data: Dict[str, Any]) -> None:
        if not data:
            raise ValueError("No data to insert")

        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        values = list(data.values())

        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(sql, values)
            await db.commit()

    async def get_data_group(
        self, table_name: str, group_key: str, group_value: Any
    ) -> List[Dict[str, Any]]:
        sql = f"SELECT * FROM {table_name} WHERE {group_key} = ?"

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(sql, (group_value,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
