"""SQLite helper for saving beta applications."""
import sqlite3
from pathlib import Path
from typing import Optional


class SQLiteHelper:
    """Helper class for SQLite operations."""

    def __init__(self, db_path: str = None):
        """Initialize SQLite helper."""
        if db_path is None:
            # Default to database/cheersai.db
            project_root = Path(__file__).parent.parent.parent
            db_path = str(project_root / "database" / "cheersai.db")
        self.db_path = db_path

    def save_beta_application(
        self,
        email: str,
        name: Optional[str] = None,
        company: Optional[str] = None,
        use_case: Optional[str] = None,
        status: str = "pending",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> bool:
        """Save beta application to SQLite database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO beta_applications 
                (email, name, company, use_case, status, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (email, name, company, use_case, status, ip_address, user_agent),
            )

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving to SQLite: {e}")
            return False

    def check_email_exists(self, email: str) -> bool:
        """Check if email already exists in beta applications."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT COUNT(*) FROM beta_applications WHERE email = ?", (email,)
            )
            count = cursor.fetchone()[0]

            conn.close()
            return count > 0
        except Exception:
            return False
