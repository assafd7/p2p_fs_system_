import requests
import json
from typing import List, Dict, Any
from datetime import datetime
import logging

class VersionServerClient:
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.logger = logging.getLogger(__name__)

    def get_latest_version(self) -> Dict[str, Any]:
        """Get the latest version from the server"""
        try:
            response = requests.get(f"{self.server_url}/latest-version")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Error getting latest version: {str(e)}")
            raise

    def get_changes_since(self, version_hash: str) -> List[Dict[str, Any]]:
        """Get all changes since a specific version"""
        try:
            response = requests.get(
                f"{self.server_url}/changes-since/{version_hash}"
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Error getting changes: {str(e)}")
            raise

    def push_changes(self, version_hash: str, parent_hash: str, peer_id: str, changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Push changes to the server"""
        try:
            data = {
                "version_hash": version_hash,
                "parent_hash": parent_hash,
                "peer_id": peer_id,
                "changes": [
                    {
                        "operation_type": change["operation_type"],
                        "table_name": change["table_name"],
                        "record_id": change["record_id"],
                        "data": change["data"],
                        "timestamp": change["timestamp"].isoformat(),
                        "peer_id": change["peer_id"]
                    }
                    for change in changes
                ]
            }
            
            response = requests.post(
                f"{self.server_url}/push-changes",
                json=data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Error pushing changes: {str(e)}")
            raise 