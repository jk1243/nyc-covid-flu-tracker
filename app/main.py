from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.database import init_db
from app.routers import cases


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="NYC Covid & Flu Tracker",
    description="Tracks weekly COVID-19 and influenza cases in New York City.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(cases.router)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", include_in_schema=False)
def serve_dashboard():
    return FileResponse("static/index.html")
