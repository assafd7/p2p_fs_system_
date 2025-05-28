# P2P File Sharing Application

A decentralized peer-to-peer file sharing application built with Python and PyQt6.

## Features

- User authentication and registration
- Decentralized P2P file sharing
- Automatic user discovery on local network
- File encryption for secure transfers
- Public and private file sharing
- Real-time online users list
- File download tracking
- Simple and intuitive user interface

## Requirements

- Python 3.8 or higher
- PyQt6
- SQLAlchemy
- Cryptography
- python-dotenv

## Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Project Structure

```
cursor_p2p/
├── src/                    # Source code
│   ├── main.py            # Application entry point
│   ├── config.py          # Configuration settings
│   ├── database/          # Database models and operations
│   ├── network/           # P2P networking code
│   ├── ui/                # User interface components
│   └── utils/             # Utility functions
├── requirements.txt        # Project dependencies
└── README.md              # This file
```

## Security

- Files are encrypted during transfer
- User authentication required for access
- Private file sharing with specific user permissions
- Secure P2P communication

## Usage

1. Run the application:
   ```bash
   python src/main.py
   ```
2. Register a new account or login
3. Start sharing files with other users on the network 