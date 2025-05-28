import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
import os
from pathlib import Path
import logging
import traceback

# Add the src directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.database import Database
from src.network.p2p import P2PNetwork
from src.ui.login_window import LoginWindow
from src.ui.main_window import MainWindow
from src.config import (
    APP_NAME, APP_VERSION, DEFAULT_PORT, MULTICAST_GROUP,
    DB_FILE, WINDOW_WIDTH, WINDOW_HEIGHT
)
from src.utils.logging_config import setup_logging

def main():
    # Setup logging
    logger = setup_logging()
    logger.info("Starting P2P File Sharing Application")
    
    try:
        # Create application
        app = QApplication(sys.argv)
        app.setApplicationName(APP_NAME)
        app.setApplicationVersion(APP_VERSION)
        logger.info(f"Application created: {APP_NAME} v{APP_VERSION}")
        
        # Initialize database
        logger.debug("Initializing database...")
        try:
            db = Database(DB_FILE)
            db.init_db()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}\n{traceback.format_exc()}")
            raise
        
        # Show login window
        logger.debug("Creating login window...")
        try:
            login_window = LoginWindow(db)
            logger.debug("Login window created, about to show it")
            result = login_window.exec()
            logger.debug(f"Login window result: {result}")
            
            if result != LoginWindow.DialogCode.Accepted:
                logger.info("Login window rejected, exiting application")
                sys.exit()
        except Exception as e:
            logger.error(f"Login window failed: {str(e)}\n{traceback.format_exc()}")
            raise
        
        # Get current user
        try:
            current_user = login_window.get_current_user()
            logger.info(f"User logged in: {current_user}")
        except Exception as e:
            logger.error(f"Failed to get current user: {str(e)}\n{traceback.format_exc()}")
            raise
        
        # Initialize network
        logger.debug("Initializing P2P network...")
        try:
            network = P2PNetwork(port=DEFAULT_PORT, multicast_group=MULTICAST_GROUP)
            logger.debug("P2P network object created")
            
            network.start()
            logger.debug("P2P network started")
            
            network.broadcast_presence(current_user)
            logger.debug("Presence broadcasted")
            
            logger.info("P2P network initialized successfully")
        except Exception as e:
            logger.error(f"Network initialization failed: {str(e)}\n{traceback.format_exc()}")
            raise
        
        # Show main window
        logger.debug("Creating main window...")
        try:
            main_window = MainWindow(db, network, current_user)
            logger.debug("Main window object created")
            
            main_window.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
            logger.debug("Main window resized")
            
            main_window.show()
            logger.info("Main window displayed successfully")
        except Exception as e:
            logger.error(f"Main window initialization failed: {str(e)}\n{traceback.format_exc()}")
            raise
        
        # Start application
        logger.info("Starting application event loop")
        try:
            sys.exit(app.exec())
        except Exception as e:
            logger.critical(f"Application event loop failed: {str(e)}\n{traceback.format_exc()}")
            raise
        
    except Exception as e:
        logger.critical(f"Application failed: {str(e)}\n{traceback.format_exc()}")
        raise

if __name__ == '__main__':
    main() 