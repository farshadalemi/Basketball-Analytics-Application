from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base

class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, nullable=True)
    file_path = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # New fields for video processing
    processing_status = Column(String, default="queued")  # "queued", "processing", "completed", "failed"
    duration = Column(Integer, nullable=True)  # Duration in seconds
    thumbnail_url = Column(String, nullable=True)
    processed_at = Column(DateTime, nullable=True)

    owner = relationship("User", back_populates="videos") 