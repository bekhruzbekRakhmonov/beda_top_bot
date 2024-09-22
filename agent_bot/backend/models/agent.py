from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from db.database import Base


class Agent(Base):
    __tablename__ = 'agents'
    id = Column(Integer, primary_key=True)
    agent_id = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    agency_id = Column(Integer, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow)
    clients = relationship("Client", back_populates="agent")
    properties = relationship("Property", back_populates="agent")
    messages = relationship("Message", back_populates="agent")
