from sqlalchemy import Column, String, Integer
from .database import Base

class Classroom(Base):
    __tablename__ = "classrooms"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    slug = Column(String, unique=True, index=True)
    subject = Column(String)
    password = Column(String)
    description = Column(String)
    color = Column(String)
    max_participants = Column(Integer)
    owner = Column(String)

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String)
    email = Column(String, nullable=True)
