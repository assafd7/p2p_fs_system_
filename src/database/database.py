import logging
import traceback
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError
import os
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime

from .models import Base, User, File, Download

logger = logging.getLogger('database')

class Database:
    def __init__(self, db_path=None):
        if db_path is None:
            # Create database in user's home directory
            home_dir = Path.home()
            db_dir = home_dir / '.p2p_fileshare'
            db_dir.mkdir(exist_ok=True)
            db_path = db_dir / 'p2p_fileshare.db'
        
        logger.debug(f"Initializing database with path: {db_path}")
        self.engine = create_engine(f'sqlite:///{db_path}')
        self.Session = scoped_session(sessionmaker(bind=self.engine))
        logger.debug("Database engine and session factory created")
    
    def init_db(self):
        """Initialize the database by creating all tables."""
        logger.debug("Creating database tables")
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Database tables created successfully")
        except SQLAlchemyError as e:
            logger.error(f"Failed to create database tables: {str(e)}\n{traceback.format_exc()}")
            raise
    
    @contextmanager
    def session_scope(self):
        """Provide a transactional scope around a series of operations."""
        session = self.Session()
        try:
            yield session
            session.commit()
            logger.debug("Session committed successfully")
        except Exception as e:
            session.rollback()
            logger.error(f"Session rolled back due to error: {str(e)}\n{traceback.format_exc()}")
            raise
        finally:
            session.close()
            logger.debug("Session closed")
    
    def get_user_by_username(self, username: str) -> User:
        """Get a user by username."""
        logger.debug(f"Getting user by username: {username}")
        with self.session_scope() as session:
            # Query the user and explicitly load all attributes
            user = session.query(User).filter(User.username == username).first()
            if user:
                # Create a new User instance with all attributes loaded
                loaded_user = User(
                    id=user.id,
                    username=user.username,
                    password_hash=user.password_hash,
                    is_online=user.is_online,
                    last_seen=user.last_seen
                )
                logger.debug(f"User found and loaded: {username}")
                return loaded_user
            else:
                logger.debug(f"User not found: {username}")
                return None
    
    def add_user(self, username: str, password_hash: str) -> User:
        """Add a new user."""
        logger.debug(f"Adding new user: {username}")
        with self.session_scope() as session:
            user = User(
                username=username,
                password_hash=password_hash,
                is_online=False,
                last_seen=datetime.utcnow()
            )
            session.add(user)
            session.flush()
            # Create a new User instance with all attributes
            new_user = User(
                id=user.id,
                username=user.username,
                password_hash=user.password_hash,
                is_online=user.is_online,
                last_seen=user.last_seen
            )
            logger.info(f"User added successfully: {username}")
            return new_user
    
    def get_file_by_id(self, file_id: int) -> File:
        """Get a file by ID."""
        logger.debug(f"Getting file by ID: {file_id}")
        with self.session_scope() as session:
            file = session.query(File).filter(File.id == file_id).first()
            if file:
                # Create a new File instance with all attributes
                loaded_file = File(
                    id=file.id,
                    name=file.name,
                    size=file.size,
                    owner_id=file.owner_id,
                    local_path=file.local_path,
                    is_public=file.is_public
                )
                logger.debug(f"File found: {file.name}")
                return loaded_file
            else:
                logger.debug(f"File not found: {file_id}")
                return None
    
    def add_file(self, name: str, size: int, owner_id: int, local_path: str, is_public: bool = False) -> File:
        """Add a new file."""
        logger.debug(f"Adding new file: {name}")
        with self.session_scope() as session:
            file = File(
                name=name,
                size=size,
                owner_id=owner_id,
                local_path=local_path,
                is_public=is_public
            )
            session.add(file)
            session.flush()
            # Create a new File instance with all attributes
            new_file = File(
                id=file.id,
                name=file.name,
                size=file.size,
                owner_id=file.owner_id,
                local_path=file.local_path,
                is_public=file.is_public
            )
            logger.info(f"File added successfully: {name}")
            return new_file
    
    def record_download(self, file_id: int, user_id: int):
        """Record a file download."""
        logger.debug(f"Recording download: file_id={file_id}, user_id={user_id}")
        with self.session_scope() as session:
            download = Download(file_id=file_id, user_id=user_id)
            session.add(download)
            logger.info(f"Download recorded successfully")
    
    def update_user_status(self, user_id: int, is_online: bool):
        """Update a user's online status."""
        logger.debug(f"Updating user status: user_id={user_id}, is_online={is_online}")
        with self.session_scope() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                user.is_online = is_online
                user.last_seen = datetime.utcnow()
                # Create a new User instance with updated attributes
                updated_user = User(
                    id=user.id,
                    username=user.username,
                    password_hash=user.password_hash,
                    is_online=user.is_online,
                    last_seen=user.last_seen
                )
                logger.info(f"User status updated successfully")
                return updated_user
            else:
                logger.warning(f"User not found for status update: {user_id}")
                return None
    
    def execute_in_session(self, func):
        """Execute a function within a database session."""
        session = self.get_session()
        try:
            result = func(session)
            session.commit()
            return result
        except SQLAlchemyError as e:
            session.rollback()
            raise e
        finally:
            self.close_session(session)
    
    def get_session(self):
        """Get a new database session."""
        return self.Session()
    
    def close_session(self, session):
        """Close a database session."""
        session.close() 