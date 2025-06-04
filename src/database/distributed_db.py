from typing import Dict, List, Any
import json
import sqlite3
from datetime import datetime
import threading
import queue
import logging
import hashlib
import os
from .server_client import VersionServerClient

class DistributedDatabase:
    def __init__(self, db_path: str, peer_id: str, server_url: str):
        self.db_path = db_path
        self.peer_id = peer_id
        self.connection = sqlite3.connect(db_path)
        self.cursor = self.connection.cursor()
        self.change_queue = queue.Queue()
        self.server_client = VersionServerClient(server_url)
        self.setup_database()
        self.logger = logging.getLogger(__name__)
        self.sync_thread = None
        self.is_running = False

    def setup_database(self):
        """Initialize the database schema"""
        # Version tracking
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS db_version (
                id INTEGER PRIMARY KEY,
                version_hash TEXT NOT NULL,
                last_sync_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                peer_id TEXT NOT NULL
            )
        ''')

        # Version history
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS version_history (
                version_hash TEXT PRIMARY KEY,
                parent_hash TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                peer_id TEXT NOT NULL,
                changes TEXT NOT NULL,
                is_snapshot BOOLEAN DEFAULT 0
            )
        ''')

        # Files table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                owner_id TEXT NOT NULL,
                last_modified DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_shared BOOLEAN DEFAULT 1,
                version_hash TEXT NOT NULL
            )
        ''')

        # Users table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                version_hash TEXT NOT NULL
            )
        ''')

        # Sync operations
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_operations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation_type TEXT NOT NULL,
                table_name TEXT NOT NULL,
                record_id TEXT NOT NULL,
                data TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                peer_id TEXT NOT NULL,
                is_applied BOOLEAN DEFAULT 0,
                version_hash TEXT NOT NULL
            )
        ''')
        
        self.connection.commit()

    def start_sync(self):
        """Start the synchronization process"""
        if not self.is_running:
            self.is_running = True
            self.sync_thread = threading.Thread(target=self._sync_loop)
            self.sync_thread.daemon = True
            self.sync_thread.start()
            self.logger.info("Database synchronization started")

    def stop_sync(self):
        """Stop the synchronization process"""
        self.is_running = False
        if self.sync_thread:
            self.sync_thread.join()
            self.logger.info("Database synchronization stopped")

    def _sync_loop(self):
        """Main synchronization loop"""
        while self.is_running:
            try:
                self._sync_with_server()
                threading.Event().wait(300)  # Sync every 5 minutes
            except Exception as e:
                self.logger.error(f"Error in sync loop: {str(e)}")
                threading.Event().wait(60)  # Wait 1 minute before retrying

    def _sync_with_server(self):
        """Synchronize with the version server"""
        try:
            # Get current version
            current_version = self.get_current_version()
            
            # Get latest version from server
            latest_version = self.server_client.get_latest_version()
            
            if current_version and current_version['version_hash'] == latest_version['version_hash']:
                return  # Already up to date
            
            # Get changes since current version
            changes = self.server_client.get_changes_since(
                current_version['version_hash'] if current_version else "0"
            )
            
            # Apply changes
            for change in changes:
                self._apply_server_changes(change)
            
            # Update version
            self.update_version(latest_version['version_hash'])
            
        except Exception as e:
            self.logger.error(f"Error syncing with server: {str(e)}")
            raise

    def _apply_server_changes(self, change: Dict[str, Any]):
        """Apply changes received from the server"""
        try:
            for operation in change['changes']:
                if operation['operation_type'] == 'INSERT':
                    self._apply_insert(
                        operation['table_name'],
                        operation['data']
                    )
                elif operation['operation_type'] == 'UPDATE':
                    self._apply_update(
                        operation['table_name'],
                        operation['record_id'],
                        operation['data']
                    )
                elif operation['operation_type'] == 'DELETE':
                    self._apply_delete(
                        operation['table_name'],
                        operation['record_id']
                    )
        except Exception as e:
            self.logger.error(f"Error applying server changes: {str(e)}")
            raise

    def apply_change(self, operation_type: str, table_name: str, record_id: str, data: Dict[str, Any]):
        """Apply a change to the local database and queue it for distribution"""
        try:
            # Apply the change locally
            if operation_type == "INSERT":
                self._apply_insert(table_name, data)
            elif operation_type == "UPDATE":
                self._apply_update(table_name, record_id, data)
            elif operation_type == "DELETE":
                self._apply_delete(table_name, record_id)

            # Calculate new version hash
            new_version_hash = self.calculate_database_hash()
            
            # Create change record
            change = {
                "operation_type": operation_type,
                "table_name": table_name,
                "record_id": record_id,
                "data": data,
                "timestamp": datetime.now(),
                "peer_id": self.peer_id
            }
            
            # Save to version history
            self.cursor.execute('''
                INSERT INTO version_history 
                (version_hash, parent_hash, peer_id, changes)
                VALUES (?, ?, ?, ?)
            ''', (
                new_version_hash,
                self.get_current_version_hash(),
                self.peer_id,
                json.dumps([change])
            ))
            
            # Push to server
            self.server_client.push_changes(
                new_version_hash,
                self.get_current_version_hash(),
                self.peer_id,
                [change]
            )
            
            self.connection.commit()
            self.change_queue.put(change)
            return True
        except Exception as e:
            self.logger.error(f"Error applying change: {str(e)}")
            return False

    def calculate_database_hash(self) -> str:
        """Calculate a hash of the current database state"""
        hash_data = []
        tables = ['files', 'users', 'sync_operations']
        for table in tables:
            self.cursor.execute(f'SELECT * FROM {table} ORDER BY id')
            records = self.cursor.fetchall()
            hash_data.extend([str(record) for record in records])
        return hashlib.sha256(''.join(hash_data).encode()).hexdigest()

    def get_current_version_hash(self) -> str:
        """Get the current version hash"""
        self.cursor.execute('SELECT version_hash FROM db_version WHERE id = 1')
        result = self.cursor.fetchone()
        return result[0] if result else None

    def update_version(self, version_hash: str):
        """Update the current version hash"""
        self.cursor.execute('''
            INSERT OR REPLACE INTO db_version (id, version_hash, peer_id)
            VALUES (1, ?, ?)
        ''', (version_hash, self.peer_id))
        self.connection.commit()

    def _apply_insert(self, table_name: str, data: Dict[str, Any]):
        """Apply an INSERT operation"""
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data])
        values = list(data.values())
        
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        self.cursor.execute(query, values)
        self.connection.commit()

    def _apply_update(self, table_name: str, record_id: str, data: Dict[str, Any]):
        """Apply an UPDATE operation"""
        set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
        values = list(data.values())
        values.append(record_id)
        
        query = f"UPDATE {table_name} SET {set_clause} WHERE id = ?"
        self.cursor.execute(query, values)
        self.connection.commit()

    def _apply_delete(self, table_name: str, record_id: str):
        """Apply a DELETE operation"""
        query = f"DELETE FROM {table_name} WHERE id = ?"
        self.cursor.execute(query, (record_id,))
        self.connection.commit()

    def get_pending_changes(self) -> List[Dict[str, Any]]:
        """Get all pending changes that need to be distributed"""
        self.cursor.execute('''
            SELECT operation_type, table_name, record_id, data, peer_id, timestamp
            FROM sync_operations
            WHERE is_applied = 0
            ORDER BY timestamp ASC
        ''')
        
        changes = []
        for row in self.cursor.fetchall():
            changes.append({
                "operation_type": row[0],
                "table_name": row[1],
                "record_id": row[2],
                "data": json.loads(row[3]),
                "peer_id": row[4],
                "timestamp": row[5]
            })
        return changes

    def mark_change_as_applied(self, change_id: int):
        """Mark a change as applied in the local database"""
        self.cursor.execute('''
            UPDATE sync_operations
            SET is_applied = 1
            WHERE id = ?
        ''', (change_id,))
        self.connection.commit()

    def close(self):
        """Close the database connection"""
        self.stop_sync()
        self.connection.close() 