import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import logging
from pathlib import Path
import hashlib
import os

logger = logging.getLogger(__name__)

class MainWindow:
    def __init__(self, root, username, storage):
        self.root = root
        self.username = username
        self.storage = storage
        
        # Initialize tree views
        self.file_tree = None
        
        self.root.title(f"P2P File Sharing - {username}")
        self.root.geometry("800x600")
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(1, weight=1)
        
        # Create toolbar
        self.create_toolbar()
        
        # Create file list
        self.create_file_list()
        
        # Center the window
        self.center_window()
        
        # Make sure the window stays on top
        self.root.lift()
        self.root.focus_force()
        
        # Initial file list refresh
        self.refresh_files()
    
    def create_toolbar(self):
        """Create the toolbar with buttons"""
        toolbar = ttk.Frame(self.main_frame)
        toolbar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(toolbar, text="Upload File", command=self.upload_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Download File", command=self.download_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Delete File", command=self.delete_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Refresh", command=self.refresh_files).pack(side=tk.LEFT, padx=5)
    
    def create_file_list(self):
        """Create the file list view"""
        # Create treeview
        columns = ("Name", "Size", "Type", "Peers")
        self.file_tree = ttk.Treeview(self.main_frame, columns=columns, show="headings")
        
        # Configure columns
        self.file_tree.heading("Name", text="Name")
        self.file_tree.heading("Size", text="Size")
        self.file_tree.heading("Type", text="Type")
        self.file_tree.heading("Peers", text="Peers")
        
        self.file_tree.column("Name", width=200)
        self.file_tree.column("Size", width=100)
        self.file_tree.column("Type", width=100)
        self.file_tree.column("Peers", width=100)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=scrollbar.set)
        
        # Grid layout
        self.file_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        
        # Bind double-click event
        self.file_tree.bind("<Double-1>", self.on_file_double_click)
        
        # Bind right-click event for context menu
        self.file_tree.bind("<Button-3>", self.show_context_menu)
    
    def center_window(self):
        """Center the window on the screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def format_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
    
    def upload_file(self):
        """Handle file upload"""
        file_path = filedialog.askopenfilename()
        if not file_path:
            return
        
        try:
            # Get file info
            file_path = Path(file_path)
            file_size = file_path.stat().st_size
            file_type = file_path.suffix[1:] if file_path.suffix else "Unknown"
            
            # Create file metadata
            file_data = {
                "filename": file_path.name,
                "size": file_size,
                "type": file_type,
                "owner": self.username,
                "peers": [self.username]  # Initially only the owner has the file
            }
            
            # Store file metadata
            self.storage.store_file_metadata(file_data)
            
            # Refresh the file list
            self.refresh_files()
            
            messagebox.showinfo("Success", f"File {file_path.name} uploaded successfully!")
            
        except Exception as e:
            logger.error(f"Upload error: {str(e)}")
            messagebox.showerror("Error", "Failed to upload file")
    
    def download_file(self):
        """Handle file download"""
        selected = self.file_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a file to download")
            return
        
        # For now, just show a message
        messagebox.showinfo("Info", "File download will be implemented in the next phase")
    
    def refresh_files(self):
        """Refresh the file list"""
        # Clear current items
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        
        try:
            # Get all files from storage
            files_data = self.storage.get_all_files()
            
            # Add files to treeview
            for file_hash, file_data in files_data.items():
                # Add a visual indicator for files owned by the current user
                filename = file_data["filename"]
                if file_data.get("owner") == self.username:
                    filename = f"📁 {filename}"  # Add folder emoji for owned files
                
                self.file_tree.insert("", tk.END, values=(
                    filename,
                    self.format_size(file_data["size"]),
                    file_data["type"],
                    len(file_data.get("peers", []))
                ))
        except Exception as e:
            logger.error(f"Error refreshing files: {str(e)}")
            messagebox.showerror("Error", "Failed to refresh file list")
    
    def on_file_double_click(self, _event):
        """Handle double-click on a file"""
        selected = self.file_tree.selection()
        if selected:
            self.download_file()
    
    def show_context_menu(self, event):
        """Show context menu on right-click"""
        # Get the item under the cursor
        item = self.file_tree.identify_row(event.y)
        if item:
            # Select the item
            self.file_tree.selection_set(item)
            
            # Create context menu
            context_menu = tk.Menu(self.root, tearoff=0)
            context_menu.add_command(label="Download", command=self.download_file)
            context_menu.add_command(label="Delete", command=self.delete_file)
            
            # Show the menu
            context_menu.post(event.x_root, event.y_root)
    
    def delete_file(self):
        """Handle file deletion"""
        selected = self.file_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a file to delete")
            return
        
        # Get the selected item's values
        item = selected[0]
        filename = self.file_tree.item(item)["values"][0]
        
        try:
            # Get all files to find the file hash
            files_data = self.storage.get_all_files()
            file_hash = None
            file_data = None
            
            # Find the file hash for the selected file
            for hash_value, data in files_data.items():
                if data["filename"] == filename:
                    file_hash = hash_value
                    file_data = data
                    break
            
            if not file_hash or not file_data:
                messagebox.showerror("Error", f"Could not find file {filename}")
                return
            
            # Check if the user is the owner
            if file_data.get("owner") != self.username:
                messagebox.showerror("Permission Denied", 
                    f"You cannot delete this file. It is owned by {file_data.get('owner')}")
                return
            
            # Confirm deletion
            if not messagebox.askyesno("Confirm Delete", 
                f"Are you sure you want to delete {filename}?"):
                return
            
            # Delete the file metadata
            if self.storage.delete_file_metadata(file_hash, self.username):
                # Refresh the file list
                self.refresh_files()
                messagebox.showinfo("Success", f"File {filename} deleted successfully")
            else:
                messagebox.showerror("Error", f"Failed to delete file {filename}")
                
        except Exception as e:
            logger.error(f"Delete error: {str(e)}")
            messagebox.showerror("Error", "Failed to delete file") 