import os
from pathlib import Path
from database.db_manager import DatabaseManager
from security.crypto import SecurityManager
from network.p2p_manager import P2PManager
from gui.app import P2PFileShareApp

def setup_directories():
    """Create necessary directories for the application."""
    directories = [
        "database",
        "uploads",
        "downloads",
        "temp"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)

def main():
    # Setup directories
    setup_directories()
    
    # Initialize components
    db_manager = DatabaseManager()
    security_manager = SecurityManager()
    p2p_manager = P2PManager()
    
    # Start P2P server
    p2p_manager.start_server()
    
    try:
        # Create and run the GUI application
        app = P2PFileShareApp()
        app.run()
    finally:
        # Cleanup
        p2p_manager.stop_server()
        db_manager.close()

if __name__ == "__main__":
    main()
