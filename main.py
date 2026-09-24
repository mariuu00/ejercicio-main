import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from dotenv import load_dotenv

from database import db
from vistas import router as vistas_router

load_dotenv(Path(__file__).resolve().parent / ".env")

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        yield
    finally:
        if db.pool is not None:
            await db.close()


app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def healthcheck():
    return {
        "status": "ok",
        "database": "configured" if os.environ.get("DATABASE_URL") else "not_configured",
    }


app.include_router(vistas_router)