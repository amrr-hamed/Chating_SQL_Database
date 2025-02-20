import uuid
import sqlite3
from pathlib import Path
from fastapi import UploadFile
from config.settings import settings

class DatabaseManager:
    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def save_database(self, file: UploadFile) -> Path:
        """Save and validate uploaded SQLite file"""
        file_ext = Path(file.filename).suffix
        if file_ext != ".sqlite":
            raise ValueError("Only .sqlite files allowed")
            
        dest_path = self.upload_dir / f"{uuid.uuid4()}.sqlite"
        
        # Save in chunks
        with open(dest_path, "wb") as buffer:
            while content := await file.read(1024 * 1024):  # 1MB chunks
                buffer.write(content)
        
        # Validate SQLite header
        if not self._validate_sqlite(dest_path):
            dest_path.unlink(missing_ok=True)
            raise ValueError("Invalid SQLite file")
            
        return dest_path

    def _validate_sqlite(self, path: Path) -> bool:
        """Check if the file is a valid SQLite database"""
        with open(path, "rb") as f:
            return f.read(16) == b"SQLite format 3\x00"

    def extract_schema(self, db_path: Path) -> dict:
        """Extract schema metadata from SQLite database"""
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cursor = conn.cursor()

        # Fetch all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]

        schema_data = {}
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()

            cursor.execute(f"PRAGMA foreign_key_list({table})")
            foreign_keys = cursor.fetchall()

            # Build schema description
            text_chunk = f"### Table: {table}\n"

            # Columns
            text_chunk += "#### Columns:\n"
            for col_id, col_name, col_type, notnull, dflt_value, pk in columns:
                constraints = []
                if notnull:
                    constraints.append("NOT NULL")
                if pk:
                    constraints.append("PRIMARY KEY")
                if dflt_value:
                    constraints.append(f"DEFAULT {dflt_value}")
                text_chunk += f"- `{col_name}` ({col_type}{', ' + ', '.join(constraints) if constraints else ''})\n"

            # Foreign Keys
            if foreign_keys:
                text_chunk += "#### Foreign Keys:\n"
                for fk_id, seq, fk_table, from_col, to_col, on_update, on_delete, _ in foreign_keys:
                    text_chunk += f"- `{from_col}` → `{fk_table}.{to_col}` (ON UPDATE: {on_update}, ON DELETE: {on_delete})\n"

            schema_data[table] = text_chunk

        conn.close()
        return schema_data
    
    def get_db_path(self, db_id: str) -> Path:
        """Get path for uploaded database"""
        path = self.upload_dir / db_id
        print(f"Looking for database at: {path.absolute()}")  # Debug line
        if not path.exists():
            raise FileNotFoundError(f"Database {db_id} not found")
        return path
