import sqlite3
from pathlib import Path
from typing import Tuple, Optional, List, Dict
from config.settings import settings

class QueryExecutionError(Exception):
    """Custom exception for query execution errors."""
    pass


class QueryExecutor:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        self.conn.row_factory = sqlite3.Row

    def execute_safe_query(self, sql: str) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """Execute read-only query with validation"""
        try:
            sql = sql.strip().split(';')[0]  # Only first statement
            if not sql.lower().startswith("select"):
                raise QueryExecutionError("Only SELECT queries allowed")

            cursor = self.conn.cursor()
            cursor.execute(sql)
            results = [dict(row) for row in cursor.fetchall()]
            return results, None
        except sqlite3.Error as e:
            raise QueryExecutionError(f"Database error: {str(e)}")
        except Exception as e:
            raise QueryExecutionError(f"Query execution failed: {str(e)}")
        finally:
            self.conn.close()
