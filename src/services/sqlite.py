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

    async def save_data(
        self,
        table_name: str,
        data: Dict[str, Any],
        replace: bool = False,
        match_fields: Optional[list[str]] = None,
    ) -> None:
        """
        Insert a dict into a table.
        If replace=True, replace existing row(s) when all match_fields match.
        """
        if not data:
            raise ValueError("No data to insert")

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute("PRAGMA synchronous = NORMAL;")
            db.row_factory = aiosqlite.Row

            columns = ", ".join(data.keys())
            placeholders = ", ".join(["?"] * len(data))
            values = list(data.values())

            if replace and match_fields:
                # Build WHERE clause for matching existing rows
                where_clause = " AND ".join([f"{f} = ?" for f in match_fields])
                match_values = [data[f] for f in match_fields]

                # Delete old rows matching the condition
                delete_sql = f"DELETE FROM {table_name} WHERE {where_clause}"
                await db.execute(delete_sql, match_values)

            sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
            await db.execute(sql, values)
            await db.commit()


    async def get_data_group(
        self,
        table_name: str,
        group_key: str | None = None,
        group_value: Any = None,
        limit: int | None = None,
        offset: int | None = None,
        search_column: str | None = None,
        search_query: str | None = None,
    ) -> List[Dict[str, Any]]:
        """Fetch rows optionally filtered by group_key = group_value, with pagination and search."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute("PRAGMA synchronous = NORMAL;")
            db.row_factory = aiosqlite.Row

            query_parts = [f"SELECT * FROM {table_name}"]
            params = []
            conditions = []

            if group_key is not None and group_value is not None:
                conditions.append(f"{group_key} = ?")
                params.append(group_value)
            
            if search_column is not None and search_query is not None:
                conditions.append(f"{search_column} LIKE ?")
                params.append(f"%{search_query}%")

            if conditions:
                query_parts.append("WHERE " + " AND ".join(conditions))

            if limit is not None:
                query_parts.append("LIMIT ?")
                params.append(limit)
            
            if offset is not None:
                query_parts.append("OFFSET ?")
                params.append(offset)

            sql = " ".join(query_parts)
            
            async with db.execute(sql, params) as cursor:
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
            
    async def get_all_counts_by_key(
        self, table_name: str, key_field: str
    ) -> dict[str, int]:
        """
        Return a dictionary mapping each unique key_field value to its row count.
        """
        sql = f"SELECT {key_field}, COUNT(*) as count FROM {table_name} GROUP BY {key_field}"

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute("PRAGMA synchronous = NORMAL;")
            db.row_factory = aiosqlite.Row

            async with db.execute(sql) as cursor:
                rows = await cursor.fetchall()
        return {row[key_field]: row["count"] for row in rows if row[key_field] is not None}
            
    async def count_data_by_key(
        self, table_name: str, key_field: str, key_value: Any
    ) -> int:
        """
        Count rows where key_field equals the given key_value.

        Returns:
            Number of matching rows.
        """
        if key_value is None:
            return 0

        sql = f"SELECT COUNT(*) as count FROM {table_name} WHERE {key_field} = ?"

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute("PRAGMA synchronous = NORMAL;")
            db.row_factory = aiosqlite.Row

            async with db.execute(sql, (key_value,)) as cursor:
                row = await cursor.fetchone()
                return row["count"] if row else 0

    async def get_grouped_injections(
        self, limit: int = 100, offset: int = 0, search_query: str | None = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch injections grouped by func_name.
        Returns: id (min), func_name, count, cwe_labels (comma separated)
        """
        where_clause = ""
        params = []
        
        if search_query:
            where_clause = "WHERE func_name LIKE ?"
            params.append(f"%{search_query}%")

        sql = f"""
            SELECT 
                MIN(id) as id,
                func_name,
                COUNT(*) as injection_count,
                GROUP_CONCAT(DISTINCT cwe_label) as cwe_labels
            FROM injections
            {where_clause}
            GROUP BY func_name
            ORDER BY injection_count DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute("PRAGMA synchronous = NORMAL;")
            db.row_factory = aiosqlite.Row
            
            async with db.execute(sql, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_grouped_validations(
        self, limit: int = 100, offset: int = 0, search_query: str | None = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch validations grouped by func_name with calculated metrics.
        """
        where_clause = ""
        params = []
        
        if search_query:
            where_clause = "WHERE func_name LIKE ?"
            params.append(f"%{search_query}%")

        sql = f"""
            SELECT 
                MIN(id) as id,
                func_name,
                COUNT(*) as validation_count,
                GROUP_CONCAT(DISTINCT cwe_label) as cwe_labels,
                (SUM(CASE WHEN is_valid THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as pass_rate,
                (SUM(plausibility) * 1.0 / (COUNT(*) * 10.0)) as plausibility_score,
                (SUM(effectiveness) * 1.0 / (COUNT(*) * 10.0)) as effectiveness_score
            FROM validations
            {where_clause}
            GROUP BY func_name
            ORDER BY validation_count DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute("PRAGMA synchronous = NORMAL;")
            db.row_factory = aiosqlite.Row
            
            async with db.execute(sql, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def delete_data_by_ids(self, table_name: str, ids: List[int]) -> int:
        """Delete rows by a list of IDs."""
        if not ids:
            return 0
            
        placeholders = ", ".join(["?"] * len(ids))
        sql = f"DELETE FROM {table_name} WHERE id IN ({placeholders})"
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute("PRAGMA synchronous = NORMAL;")
            
            async with db.execute(sql, ids) as cursor:
                await db.commit()
                return cursor.rowcount

    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """
        Get detailed statistics for the dashboard.
        """
        stats = {
            "counts": {},
            "metrics": {}
        }
        tables = ["injections", "validations", "researches", "condenser"]
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute("PRAGMA synchronous = NORMAL;")
            
            for table in tables:
                try:
                    async with db.execute(f"SELECT COUNT(*) as count FROM {table}") as cursor:
                        row = await cursor.fetchone()
                        stats["counts"][table] = row[0] if row else 0
                except Exception:
                    stats["counts"][table] = 0

            try:
                sql_metrics = """
                    SELECT 
                        (SUM(CASE WHEN is_valid THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as pass_rate,
                        AVG(plausibility) as avg_plausibility,
                        AVG(effectiveness) as avg_effectiveness
                    FROM validations
                """
                async with db.execute(sql_metrics) as cursor:
                    row = await cursor.fetchone()
                    if row and row[0] is not None:
                        stats["metrics"]["pass_rate"] = round(row[0], 2)
                        stats["metrics"]["avg_plausibility"] = round(row[1], 2)
                        stats["metrics"]["avg_effectiveness"] = round(row[2], 2)
                    else:
                        stats["metrics"]["pass_rate"] = 0
                        stats["metrics"]["avg_plausibility"] = 0
                        stats["metrics"]["avg_effectiveness"] = 0
            except Exception:
                stats["metrics"]["pass_rate"] = 0
                stats["metrics"]["avg_plausibility"] = 0
                stats["metrics"]["avg_effectiveness"] = 0

            try:
                sql_cwe = "SELECT COUNT(DISTINCT cwe_label) FROM injections"
                async with db.execute(sql_cwe) as cursor:
                    row = await cursor.fetchone()
                    stats["metrics"]["unique_cwes"] = row[0] if row else 0
            except Exception:
                stats["metrics"]["unique_cwes"] = 0
                    
        return stats
