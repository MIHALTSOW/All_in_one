from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from all_in_one.core.db import Base
from all_in_one.modules.content.utils import CategoryEnum


class Media(Base):
    __tablename__ = "media"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False, index=True)
    category = Column(Enum(CategoryEnum), nullable=False)
    photo_video_url = Column(String(1024), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_on = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="media")
    likes = relationship("Likes", back_populates="media")
