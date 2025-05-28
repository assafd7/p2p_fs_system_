from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

class Encryption:
    def __init__(self):
        self.key = None
        self.fernet = None
    
    def generate_key(self):
        """Generate a new encryption key."""
        self.key = Fernet.generate_key()
        self.fernet = Fernet(self.key)
        return self.key
    
    def derive_key(self, password, salt=None):
        """Derive an encryption key from a password."""
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        self.key = key
        self.fernet = Fernet(key)
        return salt
    
    def encrypt_data(self, data):
        """Encrypt data using the current key."""
        if not self.fernet:
            raise ValueError("No encryption key set")
        return self.fernet.encrypt(data)
    
    def decrypt_data(self, encrypted_data):
        """Decrypt data using the current key."""
        if not self.fernet:
            raise ValueError("No encryption key set")
        return self.fernet.decrypt(encrypted_data)
    
    def encrypt_file(self, file_path):
        """Encrypt a file and return the encrypted data."""
        with open(file_path, 'rb') as f:
            data = f.read()
        return self.encrypt_data(data)
    
    def decrypt_file(self, encrypted_data, output_path):
        """Decrypt data and save it to a file."""
        decrypted_data = self.decrypt_data(encrypted_data)
        with open(output_path, 'wb') as f:
            f.write(decrypted_data)
    
    def get_key(self):
        """Get the current encryption key."""
        return self.key 