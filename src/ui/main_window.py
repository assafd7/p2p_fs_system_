from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QListWidget,
    QFileDialog, QMessageBox, QComboBox, QCheckBox,
    QProgressDialog, QListWidgetItem
)
from PyQt6.QtCore import Qt, QTimer
import os
from pathlib import Path
from typing import Optional, List, Dict
import json
import logging
import traceback

from src.database.database import Database
from src.database.models import File, User
from src.network.p2p import P2PNetwork
from src.network.encryption import Encryption
from src.config import MAX_FILE_SIZE, ALLOWED_EXTENSIONS

logger = logging.getLogger('ui')

class FileItem(QListWidgetItem):
    def __init__(self, file_id: int, name: str, size: int, owner: str, is_public: bool):
        super().__init__()
        self.file_id = file_id
        self.name = name
        self.size = size
        self.owner = owner
        self.is_public = is_public
        
        # Format size for display
        size_str = self._format_size(size)
        self.setText(f"{name} ({size_str}) - Owner: {owner}")
    
    def _format_size(self, size: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

class MainWindow(QMainWindow):
    def __init__(self, db: Database, network: P2PNetwork, current_user: str):
        logger.debug("Starting MainWindow initialization")
        try:
            super().__init__()
            logger.debug("Super().__init__() completed")
            
            self.db = db
            self.network = network
            self.current_user = current_user
            logger.debug(f"Basic properties set for user: {current_user}")
            
            try:
                self.encryption = Encryption()
                logger.debug("Encryption initialized")
            except Exception as e:
                logger.error(f"Failed to initialize encryption: {str(e)}\n{traceback.format_exc()}")
                raise
            
            self.files: Dict[int, FileItem] = {}
            logger.debug("Files dictionary initialized")
            
            self.setWindowTitle("P2P File Sharing")
            self.setMinimumSize(800, 600)
            logger.debug("Window properties set")
            
            # Create central widget and layout
            try:
                central_widget = QWidget()
                self.setCentralWidget(central_widget)
                layout = QVBoxLayout(central_widget)
                logger.debug("Central widget and layout created")
            except Exception as e:
                logger.error(f"Failed to create central widget: {str(e)}\n{traceback.format_exc()}")
                raise
            
            # Create top bar with user info and online users
            try:
                top_bar = QHBoxLayout()
                self.user_label = QLabel(f"Logged in as: {current_user}")
                self.online_users_label = QLabel("Online Users: 0")
                top_bar.addWidget(self.user_label)
                top_bar.addStretch()
                top_bar.addWidget(self.online_users_label)
                layout.addLayout(top_bar)
                logger.debug("Top bar created")
            except Exception as e:
                logger.error(f"Failed to create top bar: {str(e)}\n{traceback.format_exc()}")
                raise
            
            # Create file list
            try:
                self.file_list = QListWidget()
                layout.addWidget(QLabel("Available Files:"))
                layout.addWidget(self.file_list)
                logger.debug("File list created")
            except Exception as e:
                logger.error(f"Failed to create file list: {str(e)}\n{traceback.format_exc()}")
                raise
            
            # Create search bar
            try:
                search_layout = QHBoxLayout()
                self.search_input = QLineEdit()
                self.search_input.setPlaceholderText("Search files...")
                self.search_input.textChanged.connect(self.search_files)
                search_layout.addWidget(self.search_input)
                layout.addLayout(search_layout)
                logger.debug("Search bar created")
            except Exception as e:
                logger.error(f"Failed to create search bar: {str(e)}\n{traceback.format_exc()}")
                raise
            
            # Create buttons
            try:
                button_layout = QHBoxLayout()
                self.upload_button = QPushButton("Upload File")
                self.upload_button.clicked.connect(self.upload_file)
                self.download_button = QPushButton("Download Selected")
                self.download_button.clicked.connect(self.download_file)
                self.remove_button = QPushButton("Remove Selected")
                self.remove_button.clicked.connect(self.remove_file)
                button_layout.addWidget(self.upload_button)
                button_layout.addWidget(self.download_button)
                button_layout.addWidget(self.remove_button)
                layout.addLayout(button_layout)
                logger.debug("Buttons created")
            except Exception as e:
                logger.error(f"Failed to create buttons: {str(e)}\n{traceback.format_exc()}")
                raise
            
            # Create file sharing options
            try:
                sharing_layout = QHBoxLayout()
                self.public_checkbox = QCheckBox("Public")
                self.public_checkbox.stateChanged.connect(self.update_sharing_options)
                self.user_combo = QComboBox()
                self.user_combo.setEnabled(False)
                sharing_layout.addWidget(QLabel("Share with:"))
                sharing_layout.addWidget(self.public_checkbox)
                sharing_layout.addWidget(self.user_combo)
                layout.addLayout(sharing_layout)
                logger.debug("Sharing options created")
            except Exception as e:
                logger.error(f"Failed to create sharing options: {str(e)}\n{traceback.format_exc()}")
                raise
            
            # Set up timer for updating online users
            try:
                self.update_timer = QTimer()
                self.update_timer.timeout.connect(self.update_online_users)
                self.update_timer.start(5000)  # Update every 5 seconds
                logger.debug("Update timer created and started")
            except Exception as e:
                logger.error(f"Failed to create update timer: {str(e)}\n{traceback.format_exc()}")
                raise
            
            # Initial update
            try:
                self.update_file_list()
                self.update_online_users()
                logger.debug("Initial updates completed")
            except Exception as e:
                logger.error(f"Failed to perform initial updates: {str(e)}\n{traceback.format_exc()}")
                raise
            
            logger.info("MainWindow initialization completed successfully")
            
        except Exception as e:
            logger.critical(f"MainWindow initialization failed: {str(e)}\n{traceback.format_exc()}")
            raise
    
    def update_file_list(self):
        """Update the list of available files."""
        self.file_list.clear()
        self.files.clear()
        
        # Get current user from database
        user = self.db.get_user_by_username(self.current_user)
        if not user:
            return
        
        # Get all files accessible to the user
        session = self.db.get_session()
        try:
            # Get public files
            public_files = session.query(File).filter(File.is_public == True).all()
            
            # Get private files shared with the user
            private_files = session.query(File).join(
                File.allowed_users
            ).filter(
                User.id == user.id
            ).all()
            
            # Get user's own files
            own_files = session.query(File).filter(File.owner_id == user.id).all()
            
            # Combine and deduplicate files
            all_files = set(public_files + private_files + own_files)
            
            # Add files to the list
            for file in all_files:
                item = FileItem(
                    file.id,
                    file.name,
                    file.size,
                    file.owner.username,
                    file.is_public
                )
                self.files[file.id] = item
                self.file_list.addItem(item)
        finally:
            self.db.close_session(session)
    
    def search_files(self):
        """Search files based on the search input."""
        search_text = self.search_input.text().lower()
        
        # Show all items if search is empty
        if not search_text:
            for item in self.files.values():
                item.setHidden(False)
            return
        
        # Filter items based on search text
        for item in self.files.values():
            item.setHidden(search_text not in item.name.lower())
    
    def upload_file(self):
        """Handle file upload."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File to Share",
            str(Path.home()),
            "All Files (*.*)"
        )
        
        if not file_path:
            return
        
        # Get file info
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        file_ext = os.path.splitext(file_name)[1].lower().lstrip('.')
        
        # Validate file size
        if file_size > MAX_FILE_SIZE:
            QMessageBox.warning(
                self,
                "File Too Large",
                f"File size exceeds the maximum allowed size of {MAX_FILE_SIZE / (1024*1024*1024):.1f} GB"
            )
            return
        
        # Validate file extension
        if file_ext not in ALLOWED_EXTENSIONS:
            QMessageBox.warning(
                self,
                "Invalid File Type",
                f"File type '{file_ext}' is not allowed. Allowed types: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            )
            return
        
        # Get current user
        user = self.db.get_user_by_username(self.current_user)
        if not user:
            QMessageBox.critical(self, "Error", "User not found")
            return
        
        # Add file to database
        try:
            file = self.db.add_file(
                name=file_name,
                size=file_size,
                owner_id=user.id,
                local_path=file_path,
                is_public=self.public_checkbox.isChecked()
            )
            
            # Add allowed users if not public
            if not self.public_checkbox.isChecked():
                selected_user = self.user_combo.currentText()
                if selected_user:
                    allowed_user = self.db.get_user_by_username(selected_user)
                    if allowed_user:
                        session = self.db.get_session()
                        try:
                            file.allowed_users.append(allowed_user)
                            session.commit()
                        finally:
                            self.db.close_session(session)
            
            # Update file list
            self.update_file_list()
            
            QMessageBox.information(self, "Success", "File added successfully")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add file: {str(e)}")
    
    def download_file(self):
        """Handle file download."""
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select a file to download")
            return
        
        # Get selected file
        file_item = selected_items[0]
        file = self.db.get_file_by_id(file_item.file_id)
        if not file:
            QMessageBox.critical(self, "Error", "File not found")
            return
        
        # Choose save location
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save File",
            str(Path.home() / file.name),
            "All Files (*.*)"
        )
        
        if not save_path:
            return
        
        # Create progress dialog
        progress = QProgressDialog("Downloading file...", "Cancel", 0, 100, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setAutoClose(True)
        progress.setAutoReset(True)
        
        try:
            # Request file from owner
            success = self.network.request_file(file.owner.username, file.local_path, save_path)
            
            if success:
                # Record download
                user = self.db.get_user_by_username(self.current_user)
                if user:
                    self.db.record_download(file.id, user.id)
                QMessageBox.information(self, "Success", "File downloaded successfully")
            else:
                QMessageBox.critical(self, "Error", "Failed to download file")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Download failed: {str(e)}")
    
    def remove_file(self):
        """Remove a file from sharing."""
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select a file to remove")
            return
        
        # Get selected file
        file_item = selected_items[0]
        file = self.db.get_file_by_id(file_item.file_id)
        if not file:
            QMessageBox.critical(self, "Error", "File not found")
            return
        
        # Check if user owns the file
        user = self.db.get_user_by_username(self.current_user)
        if not user or file.owner_id != user.id:
            QMessageBox.warning(self, "Warning", "You can only remove your own files")
            return
        
        # Confirm removal
        reply = QMessageBox.question(
            self,
            "Confirm Removal",
            f"Are you sure you want to remove {file.name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Remove file from database
                session = self.db.get_session()
                try:
                    session.delete(file)
                    session.commit()
                finally:
                    self.db.close_session(session)
                
                # Update file list
                self.update_file_list()
                
                QMessageBox.information(self, "Success", "File removed successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to remove file: {str(e)}")
    
    def update_sharing_options(self):
        """Update file sharing options based on checkbox state."""
        self.user_combo.setEnabled(not self.public_checkbox.isChecked())
    
    def update_online_users(self):
        """Update the list of online users."""
        online_users = self.network.get_online_users()
        self.online_users_label.setText(f"Online Users: {len(online_users)}")
        self.user_combo.clear()
        self.user_combo.addItems(online_users)
    
    def closeEvent(self, event):
        """Handle window close event."""
        logger.debug("MainWindow close event triggered")
        try:
            self.network.broadcast_absence(self.current_user)
            logger.debug("Absence broadcasted")
            super().closeEvent(event)
            logger.debug("MainWindow closed successfully")
        except Exception as e:
            logger.error(f"Exception during MainWindow close: {str(e)}\n{traceback.format_exc()}")
            raise 