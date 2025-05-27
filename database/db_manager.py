import sqlite3
import os
from pathlib import Path

class DatabaseManager:
    def __init__(self):
        self.db_path = Path("database/p2p_fileshare.db")
        self.conn = None
        self.cursor = None
        self.initialize_database()

    def initialize_database(self):
        """Initialize the database and create necessary tables if they don't exist."""
        # Ensure database directory exists
        self.db_path.parent.mkdir(exist_ok=True)
        
        self.conn = sqlite3.connect(str(self.db_path))
        self.cursor = self.conn.cursor()

        # Create users table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create files table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                owner_id INTEGER NOT NULL,
                is_public BOOLEAN NOT NULL DEFAULT 0,
                encryption_key TEXT NOT NULL,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (owner_id) REFERENCES users (id)
            )
        ''')

        # Create file_permissions table for private file access
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                FOREIGN KEY (file_id) REFERENCES files (id),
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(file_id, user_id)
            )
        ''')

        # Create downloads table for tracking
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (file_id) REFERENCES files (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        self.conn.commit()

    def add_user(self, username, password_hash, role="user"):
        """Add a new user to the database."""
        try:
            self.cursor.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (username, password_hash, role)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def get_user(self, username):
        """Get user information by username."""
        self.cursor.execute(
            "SELECT id, username, password_hash, role FROM users WHERE username = ?",
            (username,)
        )
        return self.cursor.fetchone()

    def add_file(self, filename, file_path, file_size, owner_id, is_public, encryption_key):
        """Add a new file to the database."""
        self.cursor.execute(
            """INSERT INTO files 
               (filename, file_path, file_size, owner_id, is_public, encryption_key)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (filename, file_path, file_size, owner_id, is_public, encryption_key)
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def add_file_permission(self, file_id, user_id):
        """Add permission for a user to access a private file."""
        try:
            self.cursor.execute(
                "INSERT INTO file_permissions (file_id, user_id) VALUES (?, ?)",
                (file_id, user_id)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def record_download(self, file_id, user_id):
        """Record a file download."""
        self.cursor.execute(
            "INSERT INTO downloads (file_id, user_id) VALUES (?, ?)",
            (file_id, user_id)
        )
        self.conn.commit()

    def get_accessible_files(self, user_id):
        """Get all files accessible to a user (public files and private files with permission)."""
        self.cursor.execute('''
            SELECT f.* FROM files f
            LEFT JOIN file_permissions fp ON f.id = fp.file_id
            WHERE f.is_public = 1 OR f.owner_id = ? OR fp.user_id = ?
        ''', (user_id, user_id))
        return self.cursor.fetchall()

    def search_files(self, user_id, search_term):
        """Search for files by name that are accessible to the user."""
        self.cursor.execute('''
            SELECT f.* FROM files f
            LEFT JOIN file_permissions fp ON f.id = fp.file_id
            WHERE (f.is_public = 1 OR f.owner_id = ? OR fp.user_id = ?)
            AND f.filename LIKE ?
        ''', (user_id, user_id, f'%{search_term}%'))
        return self.cursor.fetchall()

    def get_download_history(self, file_id):
        """Get download history for a specific file."""
        self.cursor.execute('''
            SELECT u.username, d.downloaded_at
            FROM downloads d
            JOIN users u ON d.user_id = u.id
            WHERE d.file_id = ?
            ORDER BY d.downloaded_at DESC
        ''', (file_id,))
        return self.cursor.fetchall()

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close() 