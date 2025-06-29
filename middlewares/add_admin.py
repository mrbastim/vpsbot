import sqlite3

class AddAdminMiddleware:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS allowed_users (
                user_id INTEGER PRIMARY KEY
            )
            """
        )
        conn.commit()
        conn.close()

    def add_admin(self, user_id: int):
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute(
                "INSERT OR IGNORE INTO allowed_users (user_id) VALUES (?)",
                (user_id,)
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error as e:
            return (False, str(e))

    def is_admin(self, user_id: int) -> bool:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM allowed_users WHERE user_id = ?", (user_id,))
        result = cur.fetchone() is not None
        conn.close()
        return result