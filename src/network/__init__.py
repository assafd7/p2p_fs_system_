"""
P2P Network Module

This module handles all peer-to-peer networking functionality including:
- DHT (Distributed Hash Table) for peer discovery
- Peer node management
- P2P communication protocol
- Peer discovery mechanism
"""

from .dht import DHT
from .peer import Peer
from .protocol import Protocol
#from .discovery import PeerDiscovery

__all__ = ['DHT', 'Peer', 'Protocol']
#__all__ = ['DHT', 'Peer', 'Protocol', 'PeerDiscovery']