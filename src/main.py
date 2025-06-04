"""
Main entry point for the P2P application
"""

import sys
import logging
from network.peer import Peer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    """Main entry point"""
    # Create and start peer
    peer = Peer("0.0.0.0", 8000)  # Listen on all interfaces
    peer.start()
    
    print("\nP2P Node Started!")
    print("Your node ID:", peer.id)
    print("Listening on port 8000")
    print("\nCommands:")
    print("  connect <ip> - Connect to another peer")
    print("  list - List connected peers")
    print("  quit - Stop the peer")
    
    while True:
        try:
            cmd = input("\nEnter command: ").strip().split()
            if not cmd:
                continue
                
            if cmd[0] == "connect" and len(cmd) == 2:
                # Connect to another peer
                ip = cmd[1]
                print(f"Connecting to {ip}:8000...")
                if peer.connect(ip, 8000):
                    print("Connected successfully!")
                else:
                    print("Connection failed!")
                    
            elif cmd[0] == "list":
                # List connected peers
                peers = peer.get_connected_peers()
                if peers:
                    print("\nConnected peers:")
                    for p in peers:
                        print(f"  {p.id} - {p.address[0]}:{p.address[1]}")
                else:
                    print("No peers connected")
                    
            elif cmd[0] == "quit":
                # Stop the peer
                peer.stop()
                print("Peer stopped")
                break
                
            else:
                print("Unknown command")
                
        except KeyboardInterrupt:
            print("\nStopping peer...")
            peer.stop()
            break
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 