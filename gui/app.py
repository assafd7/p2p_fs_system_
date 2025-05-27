import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import os
from typing import Optional, List, Dict
import threading
from pathlib import Path
from database.db_manager import DatabaseManager
from security.crypto import SecurityManager
from network.p2p_manager import P2PManager

class P2PFileShareApp:
    def __init__(self):
        self.app = ctk.CTk()
        self.app.title("P2P File Sharing")
        self.app.geometry("800x600")
        
        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Initialize managers
        self.db_manager = DatabaseManager()
        self.security_manager = SecurityManager()
        self.p2p_manager = P2PManager()
        
        # Initialize variables
        self.current_user: Optional[Dict] = None
        self.selected_file: Optional[Dict] = None
        self.selected_users: List[str] = []
        
        # Create main container
        self.main_container = ctk.CTkFrame(self.app)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Show login screen initially
        self.show_login_screen()

    def show_login_screen(self):
        """Show the login screen."""
        # Clear main container
        for widget in self.main_container.winfo_children():
            widget.destroy()
        
        # Create login frame
        login_frame = ctk.CTkFrame(self.main_container)
        login_frame.pack(pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            login_frame,
            text="P2P File Sharing",
            font=("Helvetica", 24, "bold")
        )
        title_label.pack(pady=20)
        
        # Username
        username_label = ctk.CTkLabel(login_frame, text="Username:")
        username_label.pack()
        self.username_entry = ctk.CTkEntry(login_frame, width=200)
        self.username_entry.pack(pady=5)
        
        # Password
        password_label = ctk.CTkLabel(login_frame, text="Password:")
        password_label.pack()
        self.password_entry = ctk.CTkEntry(login_frame, width=200, show="*")
        self.password_entry.pack(pady=5)
        
        # Login button
        login_button = ctk.CTkButton(
            login_frame,
            text="Login",
            command=self.handle_login
        )
        login_button.pack(pady=10)
        
        # Register button
        register_button = ctk.CTkButton(
            login_frame,
            text="Register",
            command=self.show_register_screen
        )
        register_button.pack(pady=5)

    def show_register_screen(self):
        """Show the registration screen."""
        # Clear main container
        for widget in self.main_container.winfo_children():
            widget.destroy()
        
        # Create register frame
        register_frame = ctk.CTkFrame(self.main_container)
        register_frame.pack(pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            register_frame,
            text="Register New User",
            font=("Helvetica", 24, "bold")
        )
        title_label.pack(pady=20)
        
        # Username
        username_label = ctk.CTkLabel(register_frame, text="Username:")
        username_label.pack()
        self.reg_username_entry = ctk.CTkEntry(register_frame, width=200)
        self.reg_username_entry.pack(pady=5)
        
        # Password
        password_label = ctk.CTkLabel(register_frame, text="Password:")
        password_label.pack()
        self.reg_password_entry = ctk.CTkEntry(register_frame, width=200, show="*")
        self.reg_password_entry.pack(pady=5)
        
        # Confirm Password
        confirm_label = ctk.CTkLabel(register_frame, text="Confirm Password:")
        confirm_label.pack()
        self.reg_confirm_entry = ctk.CTkEntry(register_frame, width=200, show="*")
        self.reg_confirm_entry.pack(pady=5)
        
        # Register button
        register_button = ctk.CTkButton(
            register_frame,
            text="Register",
            command=self.handle_register
        )
        register_button.pack(pady=10)
        
        # Back to login button
        back_button = ctk.CTkButton(
            register_frame,
            text="Back to Login",
            command=self.show_login_screen
        )
        back_button.pack(pady=5)

    def show_main_screen(self):
        """Show the main application screen."""
        # Clear main container
        for widget in self.main_container.winfo_children():
            widget.destroy()
        
        # Create main layout
        self.create_sidebar()
        self.create_file_list()
        self.create_upload_section()

    def create_sidebar(self):
        """Create the sidebar with user info and actions."""
        sidebar = ctk.CTkFrame(self.main_container, width=200)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        # User info
        user_frame = ctk.CTkFrame(sidebar)
        user_frame.pack(fill=tk.X, padx=5, pady=5)
        
        username_label = ctk.CTkLabel(
            user_frame,
            text=f"User: {self.current_user['username']}",
            font=("Helvetica", 12, "bold")
        )
        username_label.pack(pady=5)
        
        # Search
        search_frame = ctk.CTkFrame(sidebar)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Search files...")
        self.search_entry.pack(fill=tk.X, padx=5, pady=5)
        
        search_button = ctk.CTkButton(
            search_frame,
            text="Search",
            command=self.handle_search
        )
        search_button.pack(fill=tk.X, padx=5, pady=5)
        
        # Logout button
        logout_button = ctk.CTkButton(
            sidebar,
            text="Logout",
            command=self.handle_logout
        )
        logout_button.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

    def create_file_list(self):
        """Create the file list section."""
        file_frame = ctk.CTkFrame(self.main_container)
        file_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # File list title
        title_label = ctk.CTkLabel(
            file_frame,
            text="Available Files",
            font=("Helvetica", 16, "bold")
        )
        title_label.pack(pady=10)
        
        # File list
        self.file_listbox = tk.Listbox(
            file_frame,
            bg="#2b2b2b",
            fg="white",
            selectbackground="#1f538d",
            font=("Helvetica", 12)
        )
        self.file_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.file_listbox.bind('<<ListboxSelect>>', self.handle_file_select)
        
        # Download button
        download_button = ctk.CTkButton(
            file_frame,
            text="Download Selected",
            command=self.handle_download
        )
        download_button.pack(fill=tk.X, padx=5, pady=5)

    def create_upload_section(self):
        """Create the file upload section."""
        upload_frame = ctk.CTkFrame(self.main_container)
        upload_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        
        # Upload title
        title_label = ctk.CTkLabel(
            upload_frame,
            text="Upload File",
            font=("Helvetica", 16, "bold")
        )
        title_label.pack(pady=10)
        
        # File selection
        select_button = ctk.CTkButton(
            upload_frame,
            text="Select File",
            command=self.handle_file_select_upload
        )
        select_button.pack(fill=tk.X, padx=5, pady=5)
        
        # Selected file label
        self.selected_file_label = ctk.CTkLabel(
            upload_frame,
            text="No file selected"
        )
        self.selected_file_label.pack(pady=5)
        
        # Privacy options
        privacy_frame = ctk.CTkFrame(upload_frame)
        privacy_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.privacy_var = tk.StringVar(value="public")
        public_radio = ctk.CTkRadioButton(
            privacy_frame,
            text="Public",
            variable=self.privacy_var,
            value="public"
        )
        public_radio.pack(pady=5)
        
        private_radio = ctk.CTkRadioButton(
            privacy_frame,
            text="Private",
            variable=self.privacy_var,
            value="private"
        )
        private_radio.pack(pady=5)
        
        # User selection for private files
        self.user_listbox = tk.Listbox(
            upload_frame,
            bg="#2b2b2b",
            fg="white",
            selectbackground="#1f538d",
            font=("Helvetica", 12),
            selectmode=tk.MULTIPLE
        )
        self.user_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Upload button
        upload_button = ctk.CTkButton(
            upload_frame,
            text="Upload",
            command=self.handle_upload
        )
        upload_button.pack(fill=tk.X, padx=5, pady=5)

    def handle_login(self):
        """Handle user login."""
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
        
        user = self.db_manager.get_user(username)
        if not user:
            messagebox.showerror("Error", "User not found")
            return
        
        user_id, username, stored_hash, role = user
        if not self.security_manager.verify_password(password, stored_hash):
            messagebox.showerror("Error", "Invalid password")
            return
        
        self.current_user = {
            'id': user_id,
            'username': username,
            'role': role
        }
        self.show_main_screen()
        self.refresh_file_list()

    def handle_register(self):
        """Handle user registration."""
        username = self.reg_username_entry.get()
        password = self.reg_password_entry.get()
        confirm = self.reg_confirm_entry.get()
        
        if not all([username, password, confirm]):
            messagebox.showerror("Error", "Please fill in all fields")
            return
        
        if password != confirm:
            messagebox.showerror("Error", "Passwords do not match")
            return
        
        password_hash = self.security_manager.hash_password(password)
        if self.db_manager.add_user(username, password_hash):
            messagebox.showinfo("Success", "Registration successful! Please login.")
            self.show_login_screen()
        else:
            messagebox.showerror("Error", "Username already exists")

    def handle_logout(self):
        """Handle user logout."""
        self.current_user = None
        self.show_login_screen()

    def handle_search(self):
        """Handle file search."""
        search_term = self.search_entry.get()
        if not search_term:
            self.refresh_file_list()
            return
        
        self.file_listbox.delete(0, tk.END)
        files = self.db_manager.search_files(self.current_user['id'], search_term)
        
        for file in files:
            file_id, filename, file_path, file_size, owner_id, is_public, _, uploaded_at = file
            self.file_listbox.insert(tk.END, f"{filename} ({self.format_size(file_size)})")

    def handle_file_select(self, event):
        """Handle file selection from the list."""
        selection = self.file_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        filename = self.file_listbox.get(index).split(" (")[0]
        
        # Get file details from database
        files = self.db_manager.search_files(self.current_user['id'], filename)
        if files:
            self.selected_file = {
                'id': files[0][0],
                'filename': files[0][1],
                'path': files[0][2],
                'size': files[0][3]
            }

    def handle_download(self):
        """Handle file download."""
        if not self.selected_file:
            messagebox.showerror("Error", "Please select a file to download")
            return
        
        # Get download directory
        download_dir = Path("downloads")
        download_path = download_dir / self.selected_file['filename']
        
        # Record download in database
        self.db_manager.record_download(self.selected_file['id'], self.current_user['id'])
        
        # Download file from peer
        if self.p2p_manager.request_file("peer_id", str(self.selected_file['id']), str(download_path)):
            messagebox.showinfo("Success", f"File downloaded to {download_path}")
        else:
            messagebox.showerror("Error", "Failed to download file")

    def handle_file_select_upload(self):
        """Handle file selection for upload."""
        file_path = filedialog.askopenfilename()
        if file_path:
            self.selected_file = {
                'path': file_path,
                'name': os.path.basename(file_path)
            }
            self.selected_file_label.configure(text=self.selected_file['name'])

    def handle_upload(self):
        """Handle file upload."""
        if not self.selected_file:
            messagebox.showerror("Error", "Please select a file to upload")
            return
        
        is_public = self.privacy_var.get() == "public"
        selected_users = [self.user_listbox.get(i) for i in self.user_listbox.curselection()]
        
        # Generate encryption key for the file
        encryption_key = self.security_manager.generate_file_key()
        
        # Encrypt the file
        encrypted_data = self.security_manager.encrypt_file(
            self.selected_file['path'],
            encryption_key
        )
        
        # Save encrypted file
        upload_dir = Path("uploads")
        encrypted_path = upload_dir / f"encrypted_{self.selected_file['name']}"
        with open(encrypted_path, 'wb') as f:
            f.write(encrypted_data)
        
        # Add file to database
        file_id = self.db_manager.add_file(
            self.selected_file['name'],
            str(encrypted_path),
            os.path.getsize(self.selected_file['path']),
            self.current_user['id'],
            is_public,
            encryption_key.decode()
        )
        
        # Add permissions for selected users
        if not is_public and selected_users:
            for username in selected_users:
                user = self.db_manager.get_user(username)
                if user:
                    self.db_manager.add_file_permission(file_id, user[0])
        
        # Share file through P2P network
        self.p2p_manager.share_file(str(file_id), str(encrypted_path))
        
        messagebox.showinfo("Success", "File uploaded successfully")
        self.refresh_file_list()

    def refresh_file_list(self):
        """Refresh the file list with accessible files."""
        if not self.current_user:
            return
        
        self.file_listbox.delete(0, tk.END)
        files = self.db_manager.get_accessible_files(self.current_user['id'])
        
        for file in files:
            file_id, filename, file_path, file_size, owner_id, is_public, _, uploaded_at = file
            self.file_listbox.insert(tk.END, f"{filename} ({self.format_size(file_size)})")

    def format_size(self, size_bytes):
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"

    def run(self):
        """Run the application."""
        self.app.mainloop() 