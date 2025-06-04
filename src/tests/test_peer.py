"""
Test cases for Peer implementation
"""

import unittest
import threading
import time
from src.network.peer import Peer

class TestPeer(unittest.TestCase):
    def setUp(self):
        """Set up test cases"""
        self.peer1 = Peer("127.0.0.1", 8000)
        self.peer2 = Peer("127.0.0.1", 8001)
    
    def tearDown(self):
        """Clean up after tests"""
        if self.peer1.connected:
            self.peer1.stop()
        if self.peer2.connected:
            self.peer2.stop()
    
    def test_peer_initialization(self):
        """Test peer initialization"""
        self.assertIsNotNone(self.peer1.id)
        self.assertEqual(self.peer1.host, "127.0.0.1")
        self.assertEqual(self.peer1.port, 8000)
        self.assertFalse(self.peer1.connected)
    
    def test_peer_start_stop(self):
        """Test starting and stopping a peer"""
        # Test starting peer
        self.peer1.start()
        self.assertTrue(self.peer1.connected)
        self.assertIsNotNone(self.peer1._socket)
        self.assertIsNotNone(self.peer1._listener_thread)
        
        # Test stopping peer
        self.peer1.stop()
        self.assertFalse(self.peer1.connected)
        self.assertIsNone(self.peer1._socket)
        self.assertIsNone(self.peer1._listener_thread)
    
    def test_peer_connection(self):
        """Test connecting peers"""
        # Start both peers
        self.peer1.start()
        self.peer2.start()
        
        # Try to connect peer2 to peer1
        result = self.peer2.connect("127.0.0.1", 8000)
        self.assertTrue(result)
        
        # Check if peer2 has peer1 in its peer list
        self.assertIn(self.peer1.id, self.peer2.peers)
        
        # Check peer info
        peer_info = self.peer2.get_peer_info(self.peer1.id)
        self.assertIsNotNone(peer_info)
        self.assertEqual(peer_info.address, ("127.0.0.1", 8000))
    
    def test_peer_disconnection(self):
        """Test disconnecting peers"""
        # Start and connect peers
        self.peer1.start()
        self.peer2.start()
        self.peer2.connect("127.0.0.1", 8000)
        
        # Test disconnection
        result = self.peer2.disconnect(self.peer1.id)
        self.assertTrue(result)
        
        # Check peer status
        peer_info = self.peer2.get_peer_info(self.peer1.id)
        self.assertEqual(peer_info.status, 'offline')
    
    def test_connected_peers(self):
        """Test getting connected peers"""
        # Start and connect peers
        self.peer1.start()
        self.peer2.start()
        self.peer2.connect("127.0.0.1", 8000)
        
        # Get connected peers
        connected_peers = self.peer2.get_connected_peers()
        self.assertEqual(len(connected_peers), 1)
        self.assertEqual(connected_peers[0].id, self.peer1.id)

if __name__ == '__main__':
    unittest.main() 