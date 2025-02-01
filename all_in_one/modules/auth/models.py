# В этом модуле мы можем создавать, как SQLAlchemy модели, так и SQLModel модели. Тут только те модели, которые будут использоваться в БД. Мы их не будем использовать для сериализации и десериализации данных. Лучше сразу использовать SQLAlchemy, так как они дают более широкий функционал, который можно будет в дальнейшем использовать на крупных проектах.


from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from ...core.db import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(30), unique=True, nullable=False, index=True)
    email = Column(String(40), unique=True, nullable=False, index=True)
    full_name = Column(String(40), nullable=True)
    created_on = Column(DateTime, default=datetime.utcnow)
    updated_on = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    disabled = Column(Boolean, default=False)
    hashed_password = Column(String(60), nullable=False)
