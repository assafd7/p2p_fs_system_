# P2P File Sharing Application

A secure peer-to-peer file sharing application with user authentication and file encryption.

## Features

- User authentication with registration
- Role-based access control (Admin/Regular User)
- Secure file sharing with encryption
- Public and private file sharing options
- User-specific file access permissions
- File download tracking
- Real-time updates
- Simple file name search
- Clean and intuitive desktop interface

## Setup Instructions

1. Create a virtual environment:
```bash
python -m venv .venv
```

2. Activate the virtual environment:
- Windows:
```bash
.venv\Scripts\activate
```
- Linux/Mac:
```bash
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python main.py
```

## Project Structure

- `main.py` - Application entry point
- `database/` - Database management and models
- `gui/` - User interface components
- `network/` - P2P networking implementation
- `security/` - Encryption and security features
- `utils/` - Utility functions and helpers

## Security Features

- File encryption for secure sharing
- User authentication
- Permission-based access control
- Download tracking

## Requirements

- Python 3.8 or higher
- Dependencies listed in requirements.txt 