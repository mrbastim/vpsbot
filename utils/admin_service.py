import os
import sqlite3

from config import ADMIN_IDS, path_pc_global

DB_PATH = os.environ.get("VPSBOT_DB", os.path.join(path_pc_global, "access.db"))


class AdminService:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DB_PATH
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path, timeout=10)

    def _init_db(self):
        with self._connect() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS allowed_users (
                    user_id INTEGER PRIMARY KEY,
                    is_admin INTEGER NOT NULL DEFAULT 0
                )
            """)
            columns = {
                row[1] for row in conn.execute("PRAGMA table_info(allowed_users)")
            }
            if "is_admin" not in columns:
                conn.execute(
                    "ALTER TABLE allowed_users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0"
                )
            for admin in ADMIN_IDS:
                conn.execute(
                    "INSERT OR IGNORE INTO allowed_users (user_id, is_admin) VALUES (?, 1)",
                    (int(admin),),
                )
            conn.commit()

    def add(self, user_id: int, is_admin: bool = True) -> bool:
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT OR IGNORE INTO allowed_users (user_id, is_admin) VALUES (?, ?)",
                (user_id, int(is_admin)),
            )
            conn.commit()
            return cur.rowcount > 0

    def remove(self, user_id: int) -> bool:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM allowed_users WHERE user_id=?", (user_id,))
            conn.commit()
            return cur.rowcount > 0

    def exists(self, user_id: int) -> bool:
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT 1 FROM allowed_users WHERE user_id=?", (user_id,)
            )
            return cur.fetchone() is not None

    def is_admin(self, user_id: int) -> bool:
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT is_admin FROM allowed_users WHERE user_id=?", (user_id,)
            )
            row = cur.fetchone()
            return bool(row and row[0])
