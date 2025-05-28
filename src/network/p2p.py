import socket
import threading
import json
import time
from datetime import datetime
import struct
import os
from typing import Dict, List, Optional, Tuple

class P2PNetwork:
    def __init__(self, port: int = 5000, multicast_group: str = '224.3.29.71'):
        self.port = port
        self.multicast_group = multicast_group
        self.socket = None
        self.running = False
        self.online_users: Dict[str, Tuple[str, int]] = {}  # username -> (ip, port)
        self.file_transfer_socket = None
        self.file_transfer_port = port + 1
        
    def start(self):
        """Start the P2P network."""
        self.running = True
        
        # Create UDP socket for user discovery
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Bind to the server address
        self.socket.bind(('', self.port))
        
        # Tell the kernel to join a multicast group
        mreq = struct.pack('4sL', socket.inet_aton(self.multicast_group), socket.INADDR_ANY)
        self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        
        # Create TCP socket for file transfer
        self.file_transfer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.file_transfer_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.file_transfer_socket.bind(('', self.file_transfer_port))
        self.file_transfer_socket.listen(5)
        
        # Start listening threads
        threading.Thread(target=self._listen_for_users, daemon=True).start()
        threading.Thread(target=self._listen_for_files, daemon=True).start()
    
    def stop(self):
        """Stop the P2P network."""
        self.running = False
        if self.socket:
            self.socket.close()
        if self.file_transfer_socket:
            self.file_transfer_socket.close()
    
    def broadcast_presence(self, username: str):
        """Broadcast user presence to the network."""
        message = {
            'type': 'presence',
            'username': username,
            'timestamp': datetime.utcnow().isoformat()
        }
        self._send_multicast(message)
    
    def broadcast_absence(self, username: str):
        """Broadcast user absence to the network."""
        message = {
            'type': 'absence',
            'username': username,
            'timestamp': datetime.utcnow().isoformat()
        }
        self._send_multicast(message)
    
    def _send_multicast(self, message: dict):
        """Send a multicast message to the network."""
        try:
            self.socket.sendto(
                json.dumps(message).encode(),
                (self.multicast_group, self.port)
            )
        except Exception as e:
            print(f"Error sending multicast: {e}")
    
    def _listen_for_users(self):
        """Listen for user presence/absence messages."""
        while self.running:
            try:
                data, addr = self.socket.recvfrom(1024)
                message = json.loads(data.decode())
                
                if message['type'] == 'presence':
                    self.online_users[message['username']] = (addr[0], self.port)
                elif message['type'] == 'absence':
                    self.online_users.pop(message['username'], None)
            except Exception as e:
                print(f"Error in user discovery: {e}")
    
    def _listen_for_files(self):
        """Listen for incoming file transfer requests."""
        while self.running:
            try:
                client_socket, addr = self.file_transfer_socket.accept()
                threading.Thread(
                    target=self._handle_file_transfer,
                    args=(client_socket, addr),
                    daemon=True
                ).start()
            except Exception as e:
                print(f"Error in file transfer listener: {e}")
    
    def _handle_file_transfer(self, client_socket: socket.socket, addr: Tuple[str, int]):
        """Handle an incoming file transfer request."""
        try:
            # Receive file metadata
            metadata = json.loads(client_socket.recv(1024).decode())
            file_path = metadata['file_path']
            
            # Send file size
            file_size = os.path.getsize(file_path)
            client_socket.send(struct.pack('!Q', file_size))
            
            # Send file data
            with open(file_path, 'rb') as f:
                while True:
                    data = f.read(8192)
                    if not data:
                        break
                    client_socket.send(data)
        except Exception as e:
            print(f"Error in file transfer: {e}")
        finally:
            client_socket.close()
    
    def request_file(self, username: str, file_path: str, save_path: str) -> bool:
        """Request a file from another user."""
        if username not in self.online_users:
            return False
        
        ip, port = self.online_users[username]
        try:
            # Connect to the file transfer port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((ip, self.file_transfer_port))
            
            # Send file request metadata
            metadata = {
                'file_path': file_path
            }
            sock.send(json.dumps(metadata).encode())
            
            # Receive file size
            file_size = struct.unpack('!Q', sock.recv(8))[0]
            
            # Receive file data
            received_size = 0
            with open(save_path, 'wb') as f:
                while received_size < file_size:
                    data = sock.recv(min(8192, file_size - received_size))
                    if not data:
                        break
                    f.write(data)
                    received_size += len(data)
            
            return received_size == file_size
        except Exception as e:
            print(f"Error requesting file: {e}")
            return False
        finally:
            sock.close()
    
    def get_online_users(self) -> List[str]:
        """Get a list of online users."""
        return list(self.online_users.keys()) 