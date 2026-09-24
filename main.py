import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from dotenv import load_dotenv

from database import db
from vistas import router as vistas_router

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        await db.connect(db_url)
        app.state.database_configured = True
    else:
        app.state.database_configured = False
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