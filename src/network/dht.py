"""
Distributed Hash Table (DHT) Implementation

This module implements a Kademlia-like DHT for peer discovery and file location.
"""

import logging
import hashlib
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class Node:
    """Represents a node in the DHT network"""
    id: str  # Node ID (hash of IP:port)
    address: Tuple[str, int]  # (IP, port)
    last_seen: datetime
    files: List[str]  # List of file hashes this node has

class DHT:
    """Distributed Hash Table implementation"""
    
    def __init__(self, node_id: str, address: Tuple[str, int]):
        """
        Initialize the DHT
        
        Args:
            node_id: Unique identifier for this node
            address: (IP, port) tuple for this node
        """
        self.node_id = node_id
        self.address = address
        self.nodes: Dict[str, Node] = {}  # node_id -> Node
        self.file_locations: Dict[str, List[str]] = {}  # file_hash -> [node_ids]
        logger.info(f"Initialized DHT node {node_id} at {address}")
    
    def add_node(self, node_id: str, address: Tuple[str, int]) -> bool:
        """
        Add a new node to the DHT
        
        Args:
            node_id: Node's unique identifier
            address: (IP, port) tuple for the node
            
        Returns:
            bool: True if node was added, False if it already exists
        """
        if node_id in self.nodes:
            # Update last seen time
            self.nodes[node_id].last_seen = datetime.now()
            return False
        
        self.nodes[node_id] = Node(
            id=node_id,
            address=address,
            last_seen=datetime.now(),
            files=[]
        )
        logger.info(f"Added node {node_id} at {address}")
        return True
    
    def remove_node(self, node_id: str) -> bool:
        """
        Remove a node from the DHT
        
        Args:
            node_id: Node's unique identifier
            
        Returns:
            bool: True if node was removed, False if it didn't exist
        """
        if node_id not in self.nodes:
            return False
        
        # Remove node's files from file_locations
        for file_hash in self.nodes[node_id].files:
            if file_hash in self.file_locations:
                self.file_locations[file_hash].remove(node_id)
                if not self.file_locations[file_hash]:
                    del self.file_locations[file_hash]
        
        # Remove the node
        del self.nodes[node_id]
        logger.info(f"Removed node {node_id}")
        return True
    
    def add_file(self, file_hash: str, node_id: str) -> bool:
        """
        Register a file with a node
        
        Args:
            file_hash: Hash of the file
            node_id: ID of the node that has the file
            
        Returns:
            bool: True if file was added, False if node doesn't exist
        """
        if node_id not in self.nodes:
            return False
        
        # Add file to node's file list
        if file_hash not in self.nodes[node_id].files:
            self.nodes[node_id].files.append(file_hash)
        
        # Add node to file's location list
        if file_hash not in self.file_locations:
            self.file_locations[file_hash] = []
        if node_id not in self.file_locations[file_hash]:
            self.file_locations[file_hash].append(node_id)
        
        logger.info(f"Added file {file_hash} to node {node_id}")
        return True
    
    def remove_file(self, file_hash: str, node_id: str) -> bool:
        """
        Remove a file from a node
        
        Args:
            file_hash: Hash of the file
            node_id: ID of the node that has the file
            
        Returns:
            bool: True if file was removed, False if node or file doesn't exist
        """
        if node_id not in self.nodes:
            return False
        
        # Remove file from node's file list
        if file_hash in self.nodes[node_id].files:
            self.nodes[node_id].files.remove(file_hash)
        
        # Remove node from file's location list
        if file_hash in self.file_locations:
            if node_id in self.file_locations[file_hash]:
                self.file_locations[file_hash].remove(node_id)
            if not self.file_locations[file_hash]:
                del self.file_locations[file_hash]
        
        logger.info(f"Removed file {file_hash} from node {node_id}")
        return True
    
    def find_file(self, file_hash: str) -> List[Tuple[str, int]]:
        """
        Find nodes that have a specific file
        
        Args:
            file_hash: Hash of the file to find
            
        Returns:
            List[Tuple[str, int]]: List of (IP, port) tuples for nodes that have the file
        """
        if file_hash not in self.file_locations:
            return []
        
        return [self.nodes[node_id].address 
                for node_id in self.file_locations[file_hash]
                if node_id in self.nodes]
    
    def get_peers(self) -> List[Tuple[str, int]]:
        """
        Get all known peer addresses
        
        Returns:
            List[Tuple[str, int]]: List of (IP, port) tuples for all known peers
        """
        return [node.address for node in self.nodes.values()]
    
    def cleanup(self, max_age_seconds: int = 3600):
        """
        Remove nodes that haven't been seen in a while
        
        Args:
            max_age_seconds: Maximum age in seconds before a node is considered dead
        """
        now = datetime.now()
        dead_nodes = [
            node_id for node_id, node in self.nodes.items()
            if (now - node.last_seen).total_seconds() > max_age_seconds
        ]
        
        for node_id in dead_nodes:
            self.remove_node(node_id) 