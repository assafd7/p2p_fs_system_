import socket
import threading
import json
import os
from typing import Dict, List, Optional
import time

class P2PManager:
    def __init__(self, host: str = '0.0.0.0', port: int = 5000):
        self.host = host
        self.port = port
        self.peers: Dict[str, tuple] = {}  # {peer_id: (host, port)}
        self.server_socket: Optional[socket.socket] = None
        self.is_running = False
        self.file_chunks: Dict[str, List[bytes]] = {}  # {file_id: [chunks]}
        self.chunk_size = 1024 * 1024  # 1MB chunks

    def start_server(self):
        """Start the P2P server."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.is_running = True

        # Start listening for connections in a separate thread
        threading.Thread(target=self._listen_for_connections, daemon=True).start()

    def _listen_for_connections(self):
        """Listen for incoming connections."""
        while self.is_running:
            try:
                client_socket, address = self.server_socket.accept()
                threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, address),
                    daemon=True
                ).start()
            except Exception as e:
                if self.is_running:
                    print(f"Error accepting connection: {e}")

    def _handle_client(self, client_socket: socket.socket, address: tuple):
        """Handle incoming client connections."""
        try:
            data = client_socket.recv(1024).decode()
            request = json.loads(data)

            if request['type'] == 'file_request':
                self._handle_file_request(client_socket, request)
            elif request['type'] == 'peer_announce':
                self._handle_peer_announce(request)
            elif request['type'] == 'file_chunk':
                self._handle_file_chunk(request)

        except Exception as e:
            print(f"Error handling client {address}: {e}")
        finally:
            client_socket.close()

    def _handle_file_request(self, client_socket: socket.socket, request: dict):
        """Handle file download requests."""
        file_id = request['file_id']
        chunk_index = request.get('chunk_index', 0)

        if file_id in self.file_chunks and chunk_index < len(self.file_chunks[file_id]):
            chunk = self.file_chunks[file_id][chunk_index]
            response = {
                'type': 'file_chunk',
                'file_id': file_id,
                'chunk_index': chunk_index,
                'data': chunk.hex()
            }
            client_socket.send(json.dumps(response).encode())

    def _handle_peer_announce(self, request: dict):
        """Handle peer announcements."""
        peer_id = request['peer_id']
        host = request['host']
        port = request['port']
        self.peers[peer_id] = (host, port)

    def _handle_file_chunk(self, request: dict):
        """Handle incoming file chunks."""
        file_id = request['file_id']
        chunk_index = request['chunk_index']
        chunk_data = bytes.fromhex(request['data'])

        if file_id not in self.file_chunks:
            self.file_chunks[file_id] = []

        while len(self.file_chunks[file_id]) <= chunk_index:
            self.file_chunks[file_id].append(None)

        self.file_chunks[file_id][chunk_index] = chunk_data

    def connect_to_peer(self, peer_id: str, host: str, port: int):
        """Connect to a new peer."""
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((host, port))
            
            # Announce ourselves to the peer
            announcement = {
                'type': 'peer_announce',
                'peer_id': f"{self.host}:{self.port}",
                'host': self.host,
                'port': self.port
            }
            client_socket.send(json.dumps(announcement).encode())
            
            self.peers[peer_id] = (host, port)
            return True
        except Exception as e:
            print(f"Error connecting to peer {peer_id}: {e}")
            return False

    def request_file(self, peer_id: str, file_id: str, save_path: str):
        """Request a file from a peer."""
        if peer_id not in self.peers:
            return False

        host, port = self.peers[peer_id]
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((host, port))

            # Request file chunks
            chunk_index = 0
            while True:
                request = {
                    'type': 'file_request',
                    'file_id': file_id,
                    'chunk_index': chunk_index
                }
                client_socket.send(json.dumps(request).encode())
                
                response = json.loads(client_socket.recv(1024).decode())
                if response['type'] != 'file_chunk':
                    break

                chunk_data = bytes.fromhex(response['data'])
                if not chunk_data:
                    break

                # Save chunk to file
                with open(save_path, 'ab') as f:
                    f.write(chunk_data)

                chunk_index += 1

            return True
        except Exception as e:
            print(f"Error requesting file from peer {peer_id}: {e}")
            return False

    def share_file(self, file_id: str, file_path: str):
        """Share a file by splitting it into chunks."""
        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()

            # Split file into chunks
            chunks = [file_data[i:i + self.chunk_size] 
                     for i in range(0, len(file_data), self.chunk_size)]
            self.file_chunks[file_id] = chunks
            return True
        except Exception as e:
            print(f"Error sharing file {file_id}: {e}")
            return False

    def stop_server(self):
        """Stop the P2P server."""
        self.is_running = False
        if self.server_socket:
            self.server_socket.close() 