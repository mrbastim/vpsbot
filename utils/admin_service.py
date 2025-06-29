import sqlite3
from config import path_pc_global

class AdminService:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or f"{path_pc_global}/access.db"
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
               CREATE TABLE IF NOT EXISTS allowed_users (
                   user_id INTEGER PRIMARY KEY
               )
            """)
            conn.commit()

    def add(self, user_id: int) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "INSERT OR IGNORE INTO allowed_users (user_id) VALUES (?)",
                (user_id,)
            )
            conn.commit()
            return cur.rowcount > 0

    def exists(self, user_id: int) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "SELECT 1 FROM allowed_users WHERE user_id=?", (user_id,)
            )
            return cur.fetchone() is not None