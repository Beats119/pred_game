from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager

from app.settings import settings
from app.services.scheduler import poll_task
from app.services.redis_client import redis_client
from app.utils.logger import get_logger
import asyncio

logger = get_logger(__name__)
background_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Prediction Matcher API...")
    global background_task
    background_task = asyncio.create_task(poll_task())
    yield
    # Shutdown
    logger.info("Shutting down API and background tasks...")
    if background_task:
        background_task.cancel()
    await redis_client.client.close()

app = FastAPI(title="BDG WIN Pattern Monitor", version="2.0", lifespan=lifespan)

@app.get("/")
async def root():
    return {"message": "BDG WIN Pattern Monitor is running"}

@app.get("/health")
async def health_check():
    """Check health of background task and redis connection"""
    try:
        await redis_client.client.ping()
        redis_status = "connected"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        redis_status = "disconnected"

    return {
        "status": "ok",
        "redis": redis_status,
        "background_task": "running" if background_task and not background_task.done() else "stopped"
    }

@app.get("/history")
async def get_history(limit: int = 20):
    """Retrieve recent game history"""
    try:
        history = await redis_client.get_history(limit)
        return {"history": history, "count": len(history)}
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        raise HTTPException(status_code=500, detail="Could not retrieve history")
