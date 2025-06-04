"""
P2P Protocol Implementation

This module implements the basic protocol for peer-to-peer communication.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

@dataclass
class Message:
    """P2P message structure"""
    type: str
    data: Dict[str, Any]
    timestamp: datetime
    sender_id: str

class Protocol:
    """P2P protocol implementation"""
    
    # Message types
    MSG_HELLO = "hello"
    MSG_PEER_LIST = "peer_list"
    MSG_FILE_LIST = "file_list"
    MSG_FILE_REQUEST = "file_request"
    MSG_FILE_RESPONSE = "file_response"
    MSG_PING = "ping"
    MSG_PONG = "pong"
    MSG_GOODBYE = "goodbye"
    
    def __init__(self, peer_id: str):
        """
        Initialize the protocol
        
        Args:
            peer_id: ID of the peer using this protocol
        """
        self.peer_id = peer_id
        self.message_handlers: Dict[str, callable] = {}
    
    def create_message(self, msg_type: str, data: Dict[str, Any]) -> Message:
        """
        Create a new message
        
        Args:
            msg_type: Type of message
            data: Message data
            
        Returns:
            Message: Created message
        """
        return Message(
            type=msg_type,
            data=data,
            timestamp=datetime.now(),
            sender_id=self.peer_id
        )
    
    def serialize_message(self, message: Message) -> bytes:
        """
        Serialize a message to bytes
        
        Args:
            message: Message to serialize
            
        Returns:
            bytes: Serialized message
        """
        data = {
            "type": message.type,
            "data": message.data,
            "timestamp": message.timestamp.isoformat(),
            "sender_id": message.sender_id
        }
        return json.dumps(data).encode()
    
    def deserialize_message(self, data: bytes) -> Message:
        """
        Deserialize bytes to a message
        
        Args:
            data: Serialized message data
            
        Returns:
            Message: Deserialized message
        """
        data_dict = json.loads(data.decode())
        return Message(
            type=data_dict["type"],
            data=data_dict["data"],
            timestamp=datetime.fromisoformat(data_dict["timestamp"]),
            sender_id=data_dict["sender_id"]
        )
    
    def register_handler(self, msg_type: str, handler: callable):
        """
        Register a handler for a message type
        
        Args:
            msg_type: Type of message to handle
            handler: Function to call when message is received
        """
        self.message_handlers[msg_type] = handler
    
    def handle_message(self, message: Message) -> Optional[Message]:
        """
        Handle a received message
        
        Args:
            message: Received message
            
        Returns:
            Optional[Message]: Response message if any
        """
        if message.type in self.message_handlers:
            return self.message_handlers[message.type](message)
        else:
            logger.warning(f"No handler for message type: {message.type}")
            return None
    
    def create_hello_message(self) -> Message:
        """Create a hello message"""
        return self.create_message(self.MSG_HELLO, {
            "version": "1.0",
            "capabilities": ["file_sharing", "peer_discovery"]
        })
    
    def create_peer_list_message(self, peers: list) -> Message:
        """Create a peer list message"""
        return self.create_message(self.MSG_PEER_LIST, {
            "peers": peers
        })
    
    def create_file_list_message(self, files: list) -> Message:
        """Create a file list message"""
        return self.create_message(self.MSG_FILE_LIST, {
            "files": files
        })
    
    def create_file_request_message(self, file_id: str) -> Message:
        """Create a file request message"""
        return self.create_message(self.MSG_FILE_REQUEST, {
            "file_id": file_id
        })
    
    def create_file_response_message(self, file_id: str, data: bytes) -> Message:
        """Create a file response message"""
        return self.create_message(self.MSG_FILE_RESPONSE, {
            "file_id": file_id,
            "data": data.hex()  # Convert bytes to hex string for JSON
        })
    
    def create_ping_message(self) -> Message:
        """Create a ping message"""
        return self.create_message(self.MSG_PING, {
            "timestamp": datetime.now().isoformat()
        })
    
    def create_pong_message(self, ping_timestamp: str) -> Message:
        """Create a pong message"""
        return self.create_message(self.MSG_PONG, {
            "ping_timestamp": ping_timestamp,
            "pong_timestamp": datetime.now().isoformat()
        })
    
    def create_goodbye_message(self) -> Message:
        """Create a goodbye message"""
        return self.create_message(self.MSG_GOODBYE, {
            "reason": "normal_shutdown"
        }) 