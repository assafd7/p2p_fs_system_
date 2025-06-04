import threading
import time
import logging
from typing import Dict, List, Any
from .distributed_db import DistributedDatabase

class SyncManager:
    def __init__(self, db: DistributedDatabase, peer_network):
        self.db = db
        self.peer_network = peer_network
        self.sync_interval = 5  # seconds
        self.is_running = False
        self.sync_thread = None
        self.logger = logging.getLogger(__name__)

    def start(self):
        """Start the synchronization process"""
        if not self.is_running:
            self.is_running = True
            self.sync_thread = threading.Thread(target=self._sync_loop)
            self.sync_thread.daemon = True
            self.sync_thread.start()
            self.logger.info("Database synchronization started")

    def stop(self):
        """Stop the synchronization process"""
        self.is_running = False
        if self.sync_thread:
            self.sync_thread.join()
            self.logger.info("Database synchronization stopped")

    def _sync_loop(self):
        """Main synchronization loop"""
        while self.is_running:
            try:
                self._sync_with_peers()
                time.sleep(self.sync_interval)
            except Exception as e:
                self.logger.error(f"Error in sync loop: {str(e)}")
                time.sleep(self.sync_interval)

    def _sync_with_peers(self):
        """Synchronize database changes with all connected peers"""
        # Get pending changes from local database
        pending_changes = self.db.get_pending_changes()
        
        if not pending_changes:
            return

        # Broadcast changes to all connected peers
        for peer in self.peer_network.get_connected_peers():
            try:
                self._send_changes_to_peer(peer, pending_changes)
            except Exception as e:
                self.logger.error(f"Error sending changes to peer {peer}: {str(e)}")

    def _send_changes_to_peer(self, peer: str, changes: List[Dict[str, Any]]):
        """Send database changes to a specific peer"""
        message = {
            "type": "db_sync",
            "changes": changes,
            "sender_id": self.db.peer_id
        }
        self.peer_network.send_message(peer, message)

    def handle_sync_message(self, message: Dict[str, Any]):
        """Handle incoming database synchronization messages"""
        try:
            changes = message.get("changes", [])
            sender_id = message.get("sender_id")

            for change in changes:
                # Apply the change locally
                success = self.db.apply_change(
                    operation_type=change["operation_type"],
                    table_name=change["table_name"],
                    record_id=change["record_id"],
                    data=change["data"]
                )

                if success:
                    self.logger.info(f"Applied change from peer {sender_id}")
                else:
                    self.logger.error(f"Failed to apply change from peer {sender_id}")

        except Exception as e:
            self.logger.error(f"Error handling sync message: {str(e)}") 