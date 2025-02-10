import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from all_in_one.core.cors import get_cors_middleware
from all_in_one.modules.utils.telegram_bot import application, run_bot

from .modules.auth.routers import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    bot_task = asyncio.create_task(run_bot())

    yield

    await application.updater.stop()
    await application.stop()
    await application.shutdown()
    await bot_task


app = FastAPI(title="All in One", lifespan=lifespan)


get_cors_middleware(app)

app.include_router(auth_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
