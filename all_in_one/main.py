from fastapi import FastAPI

from .modules.auth.routers import router as auth_router

app = FastAPI(title="All in One")


app.include_router(auth_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
