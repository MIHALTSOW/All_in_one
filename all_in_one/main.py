from fastapi import FastAPI

app = FastAPI(title="All in One")


@app.get("/")
async def hello():
    return {"message": "Hello World"}
