from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship

from all_in_one.core.db import Base


class Likes(Base):
    __tablename__ = "likes"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    media_id = Column(
        Integer, ForeignKey("media.id"), nullable=False, index=True
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="likes")
    media = relationship("Media", back_populates="likes")
