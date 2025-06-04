"""
Peer Node Implementation

This module implements the peer node functionality for the P2P network.
"""

import logging
import socket
import threading
import hashlib
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass
from datetime import datetime

from .protocol import Protocol, Message

logger = logging.getLogger(__name__)

@dataclass
class PeerInfo:
    """Information about a peer node"""
    id: str
    address: Tuple[str, int]
    last_seen: datetime
    status: str  # 'online', 'offline', 'connecting'

class Peer:
    """Peer node implementation"""
    
    def __init__(self, host: str, port: int):
        """
        Initialize the peer node
        
        Args:
            host: Host address to bind to
            port: Port to bind to
        """
        self.host = host
        self.port = port
        self.id = self._generate_peer_id(host, port)
        self.peers: Dict[str, PeerInfo] = {}  # peer_id -> PeerInfo
        self.connected = False
        self._socket: Optional[socket.socket] = None
        self._listener_thread: Optional[threading.Thread] = None
        self._message_handlers: Dict[str, Callable] = {}
        
        # Initialize protocol
        self.protocol = Protocol(self.id)
        self._setup_protocol_handlers()
        
        logger.info(f"Initialized peer {self.id} at {host}:{port}")
    
    def _setup_protocol_handlers(self):
        """Set up protocol message handlers"""
        self.protocol.register_handler(Protocol.MSG_HELLO, self._handle_hello)
        self.protocol.register_handler(Protocol.MSG_PEER_LIST, self._handle_peer_list)
        self.protocol.register_handler(Protocol.MSG_FILE_LIST, self._handle_file_list)
        self.protocol.register_handler(Protocol.MSG_FILE_REQUEST, self._handle_file_request)
        self.protocol.register_handler(Protocol.MSG_FILE_RESPONSE, self._handle_file_response)
        self.protocol.register_handler(Protocol.MSG_PING, self._handle_ping)
        self.protocol.register_handler(Protocol.MSG_PONG, self._handle_pong)
        self.protocol.register_handler(Protocol.MSG_GOODBYE, self._handle_goodbye)
    
    def _generate_peer_id(self, host: str, port: int) -> str:
        """Generate a unique peer ID"""
        return hashlib.sha256(f"{host}:{port}".encode()).hexdigest()
    
    def start(self):
        """Start the peer node"""
        if self.connected:
            return
        
        try:
            # Create and bind socket
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.bind((self.host, self.port))
            self._socket.listen(5)
            
            # Start listener thread
            self._listener_thread = threading.Thread(target=self._listen, daemon=True)
            self._listener_thread.start()
            
            self.connected = True
            logger.info(f"Started peer {self.id} at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to start peer: {str(e)}")
            self.stop()
            raise
    
    def stop(self):
        """Stop the peer node"""
        self.connected = False
        
        if self._socket:
            try:
                self._socket.close()
            except:
                pass
            self._socket = None
        
        if self._listener_thread:
            self._listener_thread.join(timeout=1.0)
            self._listener_thread = None
        
        logger.info(f"Stopped peer {self.id}")
    
    def _listen(self):
        """Listen for incoming connections"""
        while self.connected:
            try:
                client_socket, address = self._socket.accept()
                threading.Thread(
                    target=self._handle_connection,
                    args=(client_socket, address),
                    daemon=True
                ).start()
            except:
                if self.connected:
                    logger.error("Error accepting connection")
    
    def _handle_connection(self, client_socket: socket.socket, address: Tuple[str, int]):
        """Handle an incoming connection"""
        try:
            # Send hello message
            hello_msg = self.protocol.create_hello_message()
            client_socket.send(self.protocol.serialize_message(hello_msg))
            
            # Handle messages
            while self.connected:
                try:
                    data = client_socket.recv(4096)
                    if not data:
                        break
                    
                    message = self.protocol.deserialize_message(data)
                    response = self.protocol.handle_message(message)
                    
                    if response:
                        client_socket.send(self.protocol.serialize_message(response))
                except:
                    break
        finally:
            client_socket.close()
    
    def connect(self, host: str, port: int) -> bool:
        """
        Connect to another peer
        
        Args:
            host: Host address to connect to
            port: Port to connect to
            
        Returns:
            bool: True if connection was successful
        """
        if not self.connected:
            return False
        
        peer_id = self._generate_peer_id(host, port)
        
        try:
            # Create connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))
            
            # Send hello message
            hello_msg = self.protocol.create_hello_message()
            sock.send(self.protocol.serialize_message(hello_msg))
            
            # Wait for response
            data = sock.recv(4096)
            if not data:
                return False
            
            response = self.protocol.deserialize_message(data)
            if response.type != Protocol.MSG_HELLO:
                return False
            
            # Update peer info
            self.peers[peer_id] = PeerInfo(
                id=peer_id,
                address=(host, port),
                last_seen=datetime.now(),
                status='online'
            )
            
            # Start connection handler
            threading.Thread(
                target=self._handle_connection,
                args=(sock, (host, port)),
                daemon=True
            ).start()
            
            logger.info(f"Connected to peer {peer_id} at {host}:{port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to peer {host}:{port}: {str(e)}")
            return False
    
    def disconnect(self, peer_id: str) -> bool:
        """
        Disconnect from a peer
        
        Args:
            peer_id: ID of the peer to disconnect from
            
        Returns:
            bool: True if disconnection was successful
        """
        if peer_id not in self.peers:
            return False
        
        # Update peer status
        self.peers[peer_id].status = 'offline'
        logger.info(f"Disconnected from peer {peer_id}")
        return True
    
    def send_message(self, peer_id: str, message: Message) -> bool:
        """
        Send a message to a peer
        
        Args:
            peer_id: ID of the peer to send to
            message: Message to send
            
        Returns:
            bool: True if message was sent successfully
        """
        if peer_id not in self.peers:
            return False
        
        # TODO: Implement message sending
        return True
    
    def get_peer_info(self, peer_id: str) -> Optional[PeerInfo]:
        """
        Get information about a peer
        
        Args:
            peer_id: ID of the peer
            
        Returns:
            Optional[PeerInfo]: Peer information if peer exists
        """
        return self.peers.get(peer_id)
    
    def get_connected_peers(self) -> List[PeerInfo]:
        """
        Get information about all connected peers
        
        Returns:
            List[PeerInfo]: List of connected peer information
        """
        return [
            info for info in self.peers.values()
            if info.status == 'online'
        ]
    
    # Protocol message handlers
    def _handle_hello(self, message: Message) -> Optional[Message]:
        """Handle hello message"""
        # Update peer info
        peer_id = message.sender_id
        if peer_id not in self.peers:
            self.peers[peer_id] = PeerInfo(
                id=peer_id,
                address=message.data.get('address', ('unknown', 0)),
                last_seen=datetime.now(),
                status='online'
            )
        
        # Send peer list in response
        return self.protocol.create_peer_list_message([
            {"id": p.id, "address": p.address}
            for p in self.get_connected_peers()
        ])
    
    def _handle_peer_list(self, message: Message) -> Optional[Message]:
        """Handle peer list message"""
        # Update peer list
        for peer in message.data.get('peers', []):
            peer_id = peer['id']
            if peer_id != self.id and peer_id not in self.peers:
                self.peers[peer_id] = PeerInfo(
                    id=peer_id,
                    address=tuple(peer['address']),
                    last_seen=datetime.now(),
                    status='online'
                )
        return None
    
    def _handle_file_list(self, message: Message) -> Optional[Message]:
        """Handle file list message"""
        # TODO: Implement file list handling
        return None
    
    def _handle_file_request(self, message: Message) -> Optional[Message]:
        """Handle file request message"""
        # TODO: Implement file request handling
        return None
    
    def _handle_file_response(self, message: Message) -> Optional[Message]:
        """Handle file response message"""
        # TODO: Implement file response handling
        return None
    
    def _handle_ping(self, message: Message) -> Optional[Message]:
        """Handle ping message"""
        return self.protocol.create_pong_message(message.data['timestamp'])
    
    def _handle_pong(self, message: Message) -> Optional[Message]:
        """Handle pong message"""
        # TODO: Update peer latency information
        return None
    
    def _handle_goodbye(self, message: Message) -> Optional[Message]:
        """Handle goodbye message"""
        peer_id = message.sender_id
        if peer_id in self.peers:
            self.peers[peer_id].status = 'offline'
        return None 