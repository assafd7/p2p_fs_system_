# P2P File Sharing Application

A peer-to-peer file sharing application built with Python and Tkinter.

## Current Features

- User registration and login
- Local file storage
- File upload and display
- Basic file metadata management

## Project Structure

```
src/
├── database/         # Local storage implementation
├── ui/              # User interface components
│   ├── login_window.py
│   └── main_window.py
└── main.py          # Application entry point
```

## Setup

1. Create a virtual environment:
```bash
python -m venv .venv
```

2. Activate the virtual environment:
- Windows:
```bash
.venv\Scripts\activate
```
- Unix/MacOS:
```bash
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python src/main.py
```

## Development Status

### Phase 1: Basic UI and Local Storage ✅
- [x] User authentication
- [x] File upload
- [x] File list display
- [x] Local storage implementation

### Phase 2: P2P Network Implementation (Next)
- [ ] DHT implementation
- [ ] Peer discovery
- [ ] P2P communication protocol
- [ ] Network status indicators

### Phase 3: File Transfer Protocol
- [ ] File chunking and reassembly
- [ ] Download progress tracking
- [ ] Parallel downloads
- [ ] File integrity verification

### Phase 4: Security & Privacy
- [ ] File encryption
- [ ] User authentication tokens
- [ ] File access control
- [ ] Secure P2P communication

### Phase 5: Advanced Features
- [ ] File search
- [ ] File versioning
- [ ] File sharing links
- [ ] Bandwidth control
- [ ] File preview
- [ ] Peer chat

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 