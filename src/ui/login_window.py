from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QDialog
)
from PyQt6.QtCore import Qt
import hashlib
import logging
import traceback

from src.database.database import Database

logger = logging.getLogger('ui')

class LoginWindow(QDialog):
    def __init__(self, db: Database):
        super().__init__()
        logger.debug("Initializing login window")
        self.db = db
        self.current_user = None
        
        self.setWindowTitle("P2P File Sharing - Login")
        self.setFixedSize(400, 200)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Username
        username_layout = QHBoxLayout()
        username_layout.addWidget(QLabel("Username:"))
        self.username_input = QLineEdit()
        username_layout.addWidget(self.username_input)
        layout.addLayout(username_layout)
        
        # Password
        password_layout = QHBoxLayout()
        password_layout.addWidget(QLabel("Password:"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        password_layout.addWidget(self.password_input)
        layout.addLayout(password_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.login)
        self.register_button = QPushButton("Register")
        self.register_button.clicked.connect(self.register)
        button_layout.addWidget(self.login_button)
        button_layout.addWidget(self.register_button)
        layout.addLayout(button_layout)
        
        # Set up enter key handling
        self.username_input.returnPressed.connect(self.login)
        self.password_input.returnPressed.connect(self.login)
        logger.debug("Login window initialized successfully")
    
    def login(self):
        """Handle login attempt."""
        try:
            username = self.username_input.text()
            password = self.password_input.text()
            
            logger.debug(f"Login attempt for user: {username}")
            
            if not username or not password:
                logger.warning("Login attempt with empty username or password")
                QMessageBox.warning(self, "Error", "Please enter both username and password")
                return
            
            # Hash the password
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            # Check credentials
            user = self.db.get_user_by_username(username)
            if user and user.password_hash == password_hash:
                logger.info(f"Successful login for user: {username}")
                self.current_user = username
                logger.debug("About to accept login window")
                self.accept()
                logger.debug("Login window accepted")
            else:
                logger.warning(f"Failed login attempt for user: {username}")
                QMessageBox.warning(self, "Error", "Invalid username or password")
        except Exception as e:
            logger.error(f"Exception during login: {str(e)}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "Error", f"Login failed: {str(e)}")
    
    def register(self):
        """Handle registration attempt."""
        try:
            username = self.username_input.text()
            password = self.password_input.text()
            
            logger.debug(f"Registration attempt for user: {username}")
            
            if not username or not password:
                logger.warning("Registration attempt with empty username or password")
                QMessageBox.warning(self, "Error", "Please enter both username and password")
                return
            
            # Check if username already exists
            if self.db.get_user_by_username(username):
                logger.warning(f"Registration attempt with existing username: {username}")
                QMessageBox.warning(self, "Error", "Username already exists")
                return
            
            # Hash the password
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            # Create new user
            self.db.add_user(username, password_hash)
            logger.info(f"Successfully registered new user: {username}")
            QMessageBox.information(self, "Success", "Registration successful! Please login.")
        except Exception as e:
            logger.error(f"Registration failed for user {username}: {str(e)}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "Error", f"Registration failed: {str(e)}")
    
    def get_current_user(self) -> str:
        """Get the current user's username."""
        logger.debug(f"Getting current user: {self.current_user}")
        return self.current_user 