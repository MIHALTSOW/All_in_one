import os

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Получение строки подключения
DATABASE_URL = os.getenv("DATABASE_URL")

# Создание асинхронного движка
engine = create_async_engine(DATABASE_URL, echo=True)

# создаем фабрику async_session для работы с асинхронными запросами к БД
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Базовый класс для моделей
Base = declarative_base()
