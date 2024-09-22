from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from db.database import Base


class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey('agents.id'), nullable=False)
    content = Column(Text, nullable=False)
    sender = Column(String, nullable=False)  # 'agent' or 'assistant'
    timestamp = Column(DateTime, default=datetime.utcnow)
    agent = relationship("Agent", back_populates="messages")
