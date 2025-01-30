from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from .db import async_session


# Функция для получения сессии базы данных
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
