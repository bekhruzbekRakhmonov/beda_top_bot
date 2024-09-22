from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from db.database import Base


class Property(Base):
    __tablename__ = 'properties'
    id = Column(Integer, primary_key=True)
    address = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    bedrooms = Column(Integer, nullable=False)
    bathrooms = Column(Integer, nullable=False)
    square_feet = Column(Float, nullable=False)
    description = Column(Text)
    agent_id = Column(Integer, ForeignKey('agents.id'), nullable=False)
    agent = relationship("Agent", back_populates="properties")
