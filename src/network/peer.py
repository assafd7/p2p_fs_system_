"""
Peer Node Implementation

This module implements the peer node functionality for the P2P network.
"""

import logging
import socket
import threading
import hashlib
import time
import json
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
        self.protocol = Protocol(self.id)
        self.peers: Dict[str, PeerInfo] = {}
        self.connected = False
        self._socket = None
        self._listener_thread = None
        
        # Register message handlers
        self.protocol.register_handler(Protocol.MSG_HELLO, self._handle_hello)
        self.protocol.register_handler(Protocol.MSG_PEER_LIST, self._handle_peer_list)
        self.protocol.register_handler(Protocol.MSG_FILE_LIST, self._handle_file_list)
        self.protocol.register_handler(Protocol.MSG_FILE_REQUEST, self._handle_file_request)
        self.protocol.register_handler(Protocol.MSG_FILE_RESPONSE, self._handle_file_response)
        self.protocol.register_handler(Protocol.MSG_PING, self._handle_ping)
        self.protocol.register_handler(Protocol.MSG_PONG, self._handle_pong)
        self.protocol.register_handler(Protocol.MSG_GOODBYE, self._handle_goodbye)
        
        logger.info(f"Initialized peer {self.id} at {host}:{port}")
    
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
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
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
                logger.info(f"New connection from {address}")
                threading.Thread(
                    target=self._handle_connection,
                    args=(client_socket, address),
                    daemon=True
                ).start()
            except Exception as e:
                if self.connected:
                    logger.error(f"Error accepting connection: {str(e)}")
    
    def _send_message(self, sock: socket.socket, message: Message) -> bool:
        """Send a message through the socket"""
        try:
            data = self.protocol.serialize_message(message)
            sock.sendall(data)
            return True
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return False
    
    def _read_message(self, sock: socket.socket) -> Optional[Message]:
        """Read a complete message from the socket"""
        try:
            # Set a short timeout for reading
            sock.settimeout(2.0)
            
            # Read the message length (first 4 bytes)
            length_data = sock.recv(4)
            if len(length_data) != 4:
                return None
                
            message_length = int.from_bytes(length_data, 'big')
            if message_length <= 0 or message_length > 1024 * 1024:  # Max 1MB
                logger.error(f"Invalid message length: {message_length}")
                return None
            
            # Read the message data
            message_data = b''
            while len(message_data) < message_length:
                chunk = sock.recv(min(4096, message_length - len(message_data)))
                if not chunk:
                    return None
                message_data += chunk
            
            # Parse the message
            return self.protocol.deserialize_message(message_data)
            
        except socket.timeout:
            logger.error("Timeout while reading message")
            return None
        except Exception as e:
            logger.error(f"Error reading message: {str(e)}")
            return None
        finally:
            sock.settimeout(None)
    
    def _handle_connection(self, client_socket: socket.socket, address: Tuple[str, int]):
        """Handle an incoming connection"""
        try:
            # Send hello message
            hello_msg = self.protocol.create_hello_message()
            if not self._send_message(client_socket, hello_msg):
                return
            
            # Wait for hello response
            response = self._read_message(client_socket)
            if not response or response.type != Protocol.MSG_HELLO:
                logger.error(f"Invalid hello response from {address}")
                return
            
            # Connection established
            peer_id = response.sender_id
            self.peers[peer_id] = PeerInfo(
                id=peer_id,
                address=address,
                last_seen=datetime.now(),
                status='online'
            )
            logger.info(f"Connection established with peer {peer_id}")
            
            # Handle messages
            while self.connected:
                message = self._read_message(client_socket)
                if not message:
                    break
                
                response = self.protocol.handle_message(message)
                if response:
                    self._send_message(client_socket, response)
                    
        except Exception as e:
            logger.error(f"Error in connection handler: {str(e)}")
        finally:
            client_socket.close()
            if peer_id in self.peers:
                self.peers[peer_id].status = 'offline'
            logger.info(f"Connection closed with {address}")
    
    def connect(self, host: str, port: int) -> bool:
        """Connect to another peer"""
        if not self.connected:
            logger.error("Cannot connect: peer is not started")
            return False
        
        logger.info(f"Connecting to {host}:{port}")
        
        try:
            # Create connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            sock.connect((host, port))
            
            # Send hello message
            hello_msg = self.protocol.create_hello_message()
            if not self._send_message(sock, hello_msg):
                return False
            
            # Wait for hello response
            response = self._read_message(sock)
            if not response or response.type != Protocol.MSG_HELLO:
                logger.error("Invalid hello response")
                return False
            
            # Connection established
            peer_id = response.sender_id
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
            
            logger.info(f"Connected to peer {peer_id}")
            return True
            
        except socket.timeout:
            logger.error("Connection timeout")
            return False
        except ConnectionRefusedError:
            logger.error("Connection refused")
            return False
        except Exception as e:
            logger.error(f"Connection failed: {str(e)}")
            return False
        finally:
            if not self.connected:
                try:
                    sock.close()
                except:
                    pass
    
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