"""
Test cases for DHT implementation
"""

import unittest
from datetime import datetime
from src.network.dht import DHT

class TestDHT(unittest.TestCase):
    def setUp(self):
        """Set up test cases"""
        self.dht = DHT("test_node", ("127.0.0.1", 8000))
    
    def test_add_node(self):
        """Test adding a node to DHT"""
        # Test adding a node
        result = self.dht.add_node("node1", ("127.0.0.1", 8001))
        self.assertTrue(result)
        self.assertIn("node1", self.dht.nodes)
        
        # Test adding duplicate node
        result = self.dht.add_node("node1", ("127.0.0.1", 8001))
        self.assertFalse(result)
    
    def test_remove_node(self):
        """Test removing a node from DHT"""
        # Add a node first
        self.dht.add_node("node1", ("127.0.0.1", 8001))
        
        # Test removing the node
        result = self.dht.remove_node("node1")
        self.assertTrue(result)
        self.assertNotIn("node1", self.dht.nodes)
        
        # Test removing non-existent node
        result = self.dht.remove_node("nonexistent")
        self.assertFalse(result)
    
    def test_add_file(self):
        """Test adding a file to DHT"""
        # Add a node first
        self.dht.add_node("node1", ("127.0.0.1", 8001))
        
        # Test adding a file
        result = self.dht.add_file("file1", "node1")
        self.assertTrue(result)
        self.assertIn("file1", self.dht.file_locations)
        self.assertIn("node1", self.dht.file_locations["file1"])
        
        # Test adding file to non-existent node
        result = self.dht.add_file("file2", "nonexistent")
        self.assertFalse(result)
    
    def test_find_file(self):
        """Test finding a file in DHT"""
        # Add a node and file
        self.dht.add_node("node1", ("127.0.0.1", 8001))
        self.dht.add_file("file1", "node1")
        
        # Test finding the file
        locations = self.dht.find_file("file1")
        self.assertEqual(len(locations), 1)
        self.assertEqual(locations[0], ("127.0.0.1", 8001))
        
        # Test finding non-existent file
        locations = self.dht.find_file("nonexistent")
        self.assertEqual(len(locations), 0)
    
    def test_cleanup(self):
        """Test cleanup of dead nodes"""
        # Add a node
        self.dht.add_node("node1", ("127.0.0.1", 8001))
        
        # Add a file to the node
        self.dht.add_file("file1", "node1")
        
        # Simulate node being dead
        self.dht.nodes["node1"].last_seen = datetime.now() - self.dht.node_timeout
        
        # Run cleanup
        self.dht.cleanup()
        
        # Check that node and its files are removed
        self.assertNotIn("node1", self.dht.nodes)
        self.assertNotIn("file1", self.dht.file_locations)

if __name__ == '__main__':
    unittest.main() 