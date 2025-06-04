from abc import ABC, abstractmethod
import json
from pathlib import Path
import hashlib
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class StorageInterface(ABC):
    """Base interface for all storage implementations"""
    
    @abstractmethod
    def start(self):
        """Initialize the storage system"""
        pass
    
    @abstractmethod
    def stop(self):
        """Cleanup the storage system"""
        pass
    
    @abstractmethod
    def store_user(self, username: str, password: str) -> bool:
        """Store a new user"""
        pass
    
    @abstractmethod
    def verify_user(self, username: str, password: str) -> bool:
        """Verify user credentials"""
        pass
    
    @abstractmethod
    def store_file_metadata(self, file_data: Dict[str, Any]) -> str:
        """Store file metadata"""
        pass
    
    @abstractmethod
    def get_file_metadata(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """Get file metadata"""
        pass
    
    @abstractmethod
    def add_peer_to_file(self, file_hash: str, peer_address: str) -> bool:
        """Add a peer to a file's peer list"""
        pass
    
    @abstractmethod
    def remove_peer_from_file(self, file_hash: str, peer_address: str) -> bool:
        """Remove a peer from a file's peer list"""
        pass

class LocalStorage(StorageInterface):
    """Local file-based storage implementation"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.users_file = self.data_dir / "users.json"
        self.files_file = self.data_dir / "files.json"
        self.files_dir = self.data_dir / "files"
        self.metadata_file = self.data_dir / "metadata.json"
        self.metadata: Dict[str, Dict[str, Any]] = {}
        self._running = False
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        """Ensure data directory and files exist"""
        self.data_dir.mkdir(exist_ok=True)
        self.files_dir.mkdir(exist_ok=True)
        if not self.users_file.exists():
            self.users_file.write_text("{}")
        if not self.files_file.exists():
            self.files_file.write_text("{}")
    
    def _hash_password(self, password: str) -> str:
        """Hash a password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def start(self):
        """Start the storage service"""
        logger.info("Starting local storage")
        self._running = True
        
        # Create necessary directories
        self.data_dir.mkdir(exist_ok=True)
        self.files_dir.mkdir(exist_ok=True)
        
        # Load existing metadata
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    self.metadata = json.load(f)
            except json.JSONDecodeError:
                logger.error("Failed to load metadata file, starting with empty storage")
                self.metadata = {}
    
    def stop(self):
        """Stop the storage service"""
        logger.info("Stopping local storage")
        self._running = False
        self.save_metadata()
    
    def save_metadata(self):
        """Save metadata to disk"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save metadata: {str(e)}")
    
    def store_user(self, username: str, password: str) -> bool:
        """Store a new user"""
        try:
            data = json.loads(self.users_file.read_text())
            if username in data:
                logger.warning(f"User {username} already exists")
                return False
            
            data[username] = {
                "username": username,
                "password_hash": self._hash_password(password),
                "created_at": str(datetime.now()),
                "files": []
            }
            self.users_file.write_text(json.dumps(data, indent=2))
            logger.info(f"Stored user {username}")
            return True
        except Exception as e:
            logger.error(f"Failed to store user: {str(e)}")
            return False
    
    def verify_user(self, username: str, password: str) -> bool:
        """Verify user credentials"""
        try:
            data = json.loads(self.users_file.read_text())
            user = data.get(username)
            if not user:
                return False
            return user["password_hash"] == self._hash_password(password)
        except Exception as e:
            logger.error(f"Failed to verify user: {str(e)}")
            return False
    
    def store_file_metadata(self, file_data: Dict[str, Any]) -> str:
        """Store file metadata and return the file hash"""
        if not self._running:
            raise RuntimeError("Storage service is not running")
        
        # Generate file hash
        file_hash = hashlib.sha256(file_data["filename"].encode()).hexdigest()
        
        # Store metadata
        self.metadata[file_hash] = file_data
        
        # Save to disk
        self.save_metadata()
        
        logger.info(f"Stored file metadata for {file_data['filename']}")
        return file_hash
    
    def get_file_metadata(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """Get file metadata by hash"""
        if not self._running:
            raise RuntimeError("Storage service is not running")
        
        return self.metadata.get(file_hash)
    
    def get_all_files(self) -> Dict[str, Dict[str, Any]]:
        """Get all stored file metadata"""
        if not self._running:
            raise RuntimeError("Storage service is not running")
        
        return self.metadata.copy()
    
    def add_peer_to_file(self, file_hash: str, peer_address: str) -> bool:
        """Add a peer to a file's peer list"""
        if not self._running:
            raise RuntimeError("Storage service is not running")
        
        try:
            data = json.loads(self.files_file.read_text())
            if file_hash not in data:
                return False
            
            if "peers" not in data[file_hash]:
                data[file_hash]["peers"] = []
            
            if peer_address not in data[file_hash]["peers"]:
                data[file_hash]["peers"].append(peer_address)
                self.files_file.write_text(json.dumps(data, indent=2))
                logger.info(f"Added peer {peer_address} to file {file_hash}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to add peer to file: {str(e)}")
            return False
    
    def remove_peer_from_file(self, file_hash: str, peer_address: str) -> bool:
        """Remove a peer from a file's peer list"""
        if not self._running:
            raise RuntimeError("Storage service is not running")
        
        try:
            data = json.loads(self.files_file.read_text())
            if file_hash not in data or "peers" not in data[file_hash]:
                return False
            
            if peer_address in data[file_hash]["peers"]:
                data[file_hash]["peers"].remove(peer_address)
                self.files_file.write_text(json.dumps(data, indent=2))
                logger.info(f"Removed peer {peer_address} from file {file_hash}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to remove peer from file: {str(e)}")
            return False
    
    def delete_file_metadata(self, file_hash: str, username: str) -> bool:
        """Delete file metadata by hash. Only the owner can delete the file."""
        if not self._running:
            raise RuntimeError("Storage service is not running")
        
        try:
            if file_hash in self.metadata:
                file_data = self.metadata[file_hash]
                filename = file_data.get("filename", "unknown")
                
                # Check if the user is the owner
                if file_data.get("owner") != username:
                    logger.warning(f"User {username} attempted to delete file {filename} owned by {file_data.get('owner')}")
                    return False
                
                # Remove from metadata
                del self.metadata[file_hash]
                
                # Save changes
                self.save_metadata()
                
                logger.info(f"Deleted file metadata for {filename} by owner {username}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete file metadata: {str(e)}")
            return False 