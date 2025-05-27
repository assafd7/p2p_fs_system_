import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

class SecurityManager:
    def __init__(self):
        self.salt = b'p2p_fileshare_salt'  # In production, use a secure random salt

    def generate_key(self, password: str) -> bytes:
        """Generate an encryption key from a password."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def encrypt_file(self, file_path: str, key: bytes) -> bytes:
        """Encrypt a file using the provided key."""
        fernet = Fernet(key)
        with open(file_path, 'rb') as file:
            file_data = file.read()
        encrypted_data = fernet.encrypt(file_data)
        return encrypted_data

    def decrypt_file(self, encrypted_data: bytes, key: bytes) -> bytes:
        """Decrypt file data using the provided key."""
        fernet = Fernet(key)
        decrypted_data = fernet.decrypt(encrypted_data)
        return decrypted_data

    def hash_password(self, password: str) -> str:
        """Hash a password for storage."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        key = kdf.derive(password.encode())
        return base64.b64encode(key).decode()

    def verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify a password against its stored hash."""
        try:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=self.salt,
                iterations=100000,
            )
            key = kdf.derive(password.encode())
            return base64.b64encode(key).decode() == stored_hash
        except Exception:
            return False

    def generate_file_key(self) -> bytes:
        """Generate a new encryption key for a file."""
        return Fernet.generate_key() 