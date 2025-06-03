import tkinter as tk
import logging
from src.ui.login_window import LoginWindow
from src.ui.main_window import MainWindow
from src.database.storage import LocalStorage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class Application:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the main window initially
        
        # Initialize storage
        self.storage = LocalStorage()
        self.storage.start()
        
        # Initialize window attributes
        self.login_window = None
        self.main_window = None
        
        # Show login window
        self.show_login()
    
    def show_login(self):
        """Show the login window"""
        self.login_window = tk.Toplevel(self.root)
        self.login_window.protocol("WM_DELETE_WINDOW", self.on_closing)  # Handle window closing
        LoginWindow(self.login_window, self.on_login_success)
    
    def on_login_success(self, username):
        """Handle successful login"""
        logger.info(f"User {username} logged in successfully")
        self.login_window.destroy()  # Close login window
        self.show_main_window(username)
    
    def show_main_window(self, username):
        """Show the main application window"""
        self.main_window = tk.Toplevel(self.root)
        self.main_window.protocol("WM_DELETE_WINDOW", self.on_closing)  # Handle window closing
        MainWindow(self.main_window, username, self.storage)
    
    def on_closing(self):
        """Handle application closing"""
        logger.info("Application closing")
        self.storage.stop()
        self.root.quit()
    
    def run(self):
        """Run the application"""
        try:
            self.root.mainloop()
        finally:
            self.storage.stop()

if __name__ == "__main__":
    app = Application()
    app.run() 