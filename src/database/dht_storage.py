from kademlia.network import Server
from kademlia.storage import IStorage
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any
import hashlib
from pathlib import Path
import websockets
import threading
import time

logger = logging.getLogger(__name__)

class DHTStorage:
    def __init__(self, host: str = "0.0.0.0", port: int = 8468):
        self.host = host
        self.port = port
        self.server = Server(storage=CustomStorage())
        self.bootstrap_nodes = []
        self._event_loop = None
        self._server_thread = None
        self._is_ready = False
        self._ready_event = threading.Event()
        
    def start(self):
        """Start the DHT server in a separate thread"""
        def run_server():
            try:
                self._event_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._event_loop)
                
                async def _start():
                    try:
                        await self.server.listen(self.port)
                        if self.bootstrap_nodes:
                            await self.server.bootstrap(self.bootstrap_nodes)
                            logger.info(f"Bootstrapped with nodes: {self.bootstrap_nodes}")
                        self._is_ready = True
                        self._ready_event.set()
                    except Exception as e:
                        logger.error(f"Failed to start server: {str(e)}")
                        self._ready_event.set()
                        raise
                
                # Start the server
                self._event_loop.run_until_complete(_start())
                
                # Run the event loop
                self._event_loop.run_forever()
            except Exception as e:
                logger.error(f"Error in server thread: {str(e)}")
                self._ready_event.set()  # Signal that we're done, even if there was an error
                raise

        self._server_thread = threading.Thread(target=run_server, daemon=True)
        self._server_thread.start()
        
        # Wait for server to be ready (with timeout)
        if not self._ready_event.wait(timeout=5):
            logger.error("DHT server failed to start within timeout")
            raise RuntimeError("DHT server failed to start")
            
        logger.info(f"DHT server started on {self.host}:{self.port}")

    def stop(self):
        """Stop the DHT server"""
        try:
            if self._event_loop:
                self._event_loop.call_soon_threadsafe(self.server.stop)
            if self._server_thread:
                self._server_thread.join(timeout=5)
            logger.info("DHT server stopped")
        except Exception as e:
            logger.error(f"Error stopping DHT server: {str(e)}")

    def _generate_key(self, data: str) -> str:
        """Generate a SHA-256 hash key for the data"""
        return hashlib.sha256(data.encode()).hexdigest()

    async def store_file_metadata(self, file_data: Dict[str, Any]) -> str:
        """Store file metadata in DHT"""
        if not self._is_ready:
            raise RuntimeError("DHT server is not ready")
            
        try:
            file_hash = self._generate_key(file_data["filename"])
            key = f"file:{file_hash}"
            value = json.dumps(file_data)
            await self.server.set(key, value)
            logger.info(f"Stored file metadata for {file_data['filename']}")
            return file_hash
        except Exception as e:
            logger.error(f"Failed to store file metadata: {str(e)}")
            raise

    async def get_file_metadata(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """Retrieve file metadata from DHT"""
        if not self._is_ready:
            raise RuntimeError("DHT server is not ready")
            
        try:
            key = f"file:{file_hash}"
            value = await self.server.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Failed to get file metadata: {str(e)}")
            return None

    async def store_user_data(self, username: str, user_data: Dict[str, Any]) -> bool:
        """Store user data in DHT"""
        if not self._is_ready:
            raise RuntimeError("DHT server is not ready")
            
        try:
            key = f"user:{username}"
            value = json.dumps(user_data)
            await self.server.set(key, value)
            logger.info(f"Stored user data for {username}")
            return True
        except Exception as e:
            logger.error(f"Failed to store user data: {str(e)}")
            return False

    async def get_user_data(self, username: str) -> Optional[Dict[str, Any]]:
        """Retrieve user data from DHT"""
        if not self._is_ready:
            raise RuntimeError("DHT server is not ready")
            
        try:
            key = f"user:{username}"
            value = await self.server.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Failed to get user data: {str(e)}")
            return None

    async def add_peer_to_file(self, file_hash: str, peer_address: str) -> bool:
        """Add a peer to the file's peer list"""
        if not self._is_ready:
            raise RuntimeError("DHT server is not ready")
            
        try:
            metadata = await self.get_file_metadata(file_hash)
            if metadata:
                if "peers" not in metadata:
                    metadata["peers"] = []
                if peer_address not in metadata["peers"]:
                    metadata["peers"].append(peer_address)
                await self.store_file_metadata(metadata)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to add peer to file: {str(e)}")
            return False

    async def remove_peer_from_file(self, file_hash: str, peer_address: str) -> bool:
        """Remove a peer from the file's peer list"""
        if not self._is_ready:
            raise RuntimeError("DHT server is not ready")
            
        try:
            metadata = await self.get_file_metadata(file_hash)
            if metadata and "peers" in metadata:
                if peer_address in metadata["peers"]:
                    metadata["peers"].remove(peer_address)
                await self.store_file_metadata(metadata)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to remove peer from file: {str(e)}")
            return False

class CustomStorage(IStorage):
    """Custom storage implementation for Kademlia"""
    def __init__(self):
        self.data = {}

    def get(self, key):
        return self.data.get(key)

    def set(self, key, value):
        self.data[key] = value

    def delete(self, key):
        if key in self.data:
            del self.data[key] 