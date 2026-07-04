from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="Tanishuv Bot Admin",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory="web/static"), name="static")


@app.get("/")
async def root():
    return {
        "status": "online",
        "name": "Tanishuv Bot Admin Panel"
    }
