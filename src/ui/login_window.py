from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QDialog
)
from PyQt6.QtCore import Qt
import hashlib
import logging
import traceback
import tkinter as tk
from tkinter import ttk, messagebox
import asyncio
from datetime import datetime

from src.database.database import Database
from src.database.dht_storage import DHTStorage
from src.database.storage import LocalStorage

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

class LoginWindowTkinter:
    def __init__(self, root=None):
        self.username = None
        self.password = None
        self.success = False
        self.root = root or tk.Tk()
        self.root.title("P2P File Sharing - Login")
        self.root.geometry("350x250")
        self.root.resizable(False, False)
        
        # Initialize DHT storage
        try:
            self.dht = DHTStorage()
            self.dht.start()
        except Exception as e:
            logger.error(f"Failed to initialize DHT storage: {str(e)}")
            messagebox.showerror("Error", "Failed to initialize storage system. Please try again.")
            self.root.destroy()
            return

        frame = ttk.Frame(self.root, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        # Username
        ttk.Label(frame, text="Username:").grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        self.username_entry = ttk.Entry(frame, width=25)
        self.username_entry.grid(row=0, column=1, pady=(0, 10))
        self.username_entry.focus()

        # Password
        ttk.Label(frame, text="Password:").grid(row=1, column=0, sticky=tk.W)
        self.password_entry = ttk.Entry(frame, width=25, show="*")
        self.password_entry.grid(row=1, column=1)

        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        self.login_button = ttk.Button(button_frame, text="Login", command=self.try_login)
        self.login_button.pack(side=tk.LEFT, padx=5)
        
        self.register_button = ttk.Button(button_frame, text="Register", command=self.try_register)
        self.register_button.pack(side=tk.LEFT, padx=5)

        self.root.bind('<Return>', lambda event: self.try_login())

    def _hash_password(self, password: str) -> str:
        """Hash the password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def _verify_credentials(self, username: str, password: str) -> bool:
        """Verify user credentials against DHT storage"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            user_data = loop.run_until_complete(self.dht.get_user_data(username))
            if user_data and user_data.get("password_hash") == self._hash_password(password):
                return True
            return False
        except Exception as e:
            logger.error(f"Error verifying credentials: {str(e)}")
            return False
        finally:
            loop.close()

    def _register_user(self, username: str, password: str) -> bool:
        """Register a new user in DHT storage"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Check if user already exists
            existing_user = loop.run_until_complete(self.dht.get_user_data(username))
            if existing_user:
                logger.warning(f"User {username} already exists")
                return False
            
            # Create user data
            user_data = {
                "username": username,
                "password_hash": self._hash_password(password),
                "created_at": str(datetime.now()),
                "files": []
            }
            
            # Store in DHT
            success = loop.run_until_complete(self.dht.store_user_data(username, user_data))
            if success:
                logger.info(f"Successfully registered user {username}")
            return success
        except Exception as e:
            logger.error(f"Error registering user: {str(e)}")
            return False
        finally:
            loop.close()

    def try_login(self):
        """Handle login attempt"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            messagebox.showwarning("Missing Information", "Please enter both username and password.")
            return
        
        # Verify credentials
        if self._verify_credentials(username, password):
            self.username = username
            self.password = password
            self.success = True
            self.root.quit()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")

    def try_register(self):
        """Handle registration attempt"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            messagebox.showwarning("Missing Information", "Please enter both username and password.")
            return
        
        if len(password) < 6:
            messagebox.showwarning("Weak Password", "Password must be at least 6 characters long.")
            return
        
        # Try to register
        if self._register_user(username, password):
            messagebox.showinfo("Success", "Registration successful! Please login.")
            self.password_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Registration Failed", "Username already exists.")

    def show(self):
        """Show the login window and return username if successful"""
        self.root.mainloop()
        if self.success:
            self.root.destroy()
            return self.username
        else:
            self.root.destroy()
            return None

    def __del__(self):
        """Cleanup when the window is destroyed"""
        try:
            if hasattr(self, 'dht'):
                self.dht.stop()
        except:
            pass 

class LoginWindow:
    def __init__(self, root, on_login_success):
        self.root = root
        self.root.title("P2P File Sharing - Login")
        self.root.geometry("400x300")
        self.on_login_success = on_login_success
        
        # Initialize storage
        self.storage = LocalStorage()
        self.storage.start()
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Username
        ttk.Label(self.main_frame, text="Username:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.username_var = tk.StringVar()
        self.username_entry = ttk.Entry(self.main_frame, textvariable=self.username_var)
        self.username_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Password
        ttk.Label(self.main_frame, text="Password:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(self.main_frame, textvariable=self.password_var, show="*")
        self.password_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Buttons
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        ttk.Button(self.button_frame, text="Login", command=self.login).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame, text="Register", command=self.register).pack(side=tk.LEFT, padx=5)
        
        # Bind Enter key to login
        self.root.bind('<Return>', lambda e: self.login())
        
        # Center the window
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
        
        try:
            if self.storage.verify_user(username, password):
                logger.info(f"User {username} logged in successfully")
                self.storage.stop()
                self.on_login_success(username)
            else:
                messagebox.showerror("Error", "Invalid username or password")
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            messagebox.showerror("Error", "An error occurred during login")
    
    def register(self):
        username = self.username_var.get().strip()
        password = self.password_var.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
        
        if len(password) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters long")
            return
        
        try:
            if self.storage.store_user(username, password):
                messagebox.showinfo("Success", "Registration successful! You can now login.")
                self.password_var.set("")  # Clear password field
            else:
                messagebox.showerror("Error", "Username already exists")
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            messagebox.showerror("Error", "An error occurred during registration")
    
    def cleanup(self):
        """Cleanup resources"""
        self.storage.stop() 