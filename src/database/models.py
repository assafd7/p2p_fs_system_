from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, DateTime, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

# Association table for file permissions
file_permissions = Table('file_permissions', Base.metadata,
    Column('file_id', Integer, ForeignKey('files.id')),
    Column('user_id', Integer, ForeignKey('users.id'))
)

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    is_admin = Column(Boolean, default=False)
    is_online = Column(Boolean, default=False)
    last_seen = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    shared_files = relationship('File', back_populates='owner')
    accessible_files = relationship('File',
                                  secondary=file_permissions,
                                  back_populates='allowed_users')
    downloads = relationship('Download', back_populates='user')

class File(Base):
    __tablename__ = 'files'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    size = Column(Integer, nullable=False)  # Size in bytes
    owner_id = Column(Integer, ForeignKey('users.id'))
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    local_path = Column(String(512), nullable=False)  # Path to file on owner's machine
    
    # Relationships
    owner = relationship('User', back_populates='shared_files')
    allowed_users = relationship('User',
                               secondary=file_permissions,
                               back_populates='accessible_files')
    downloads = relationship('Download', back_populates='file')

class Download(Base):
    __tablename__ = 'downloads'
    
    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey('files.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    downloaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    file = relationship('File', back_populates='downloads')
    user = relationship('User', back_populates='downloads') 