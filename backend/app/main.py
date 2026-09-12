import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.db.database import init_db
from backend.app.services.retrieval import HybridRetriever
from backend.app.api.routes import router as api_router

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("Starting up The Lenny Growth Assistant API...")
    # Initialize DB tables
    await init_db()
    # Warm up Hybrid Retriever index
    retriever = HybridRetriever.get_instance()
    logger.info(f"Retriever warmed up with {len(retriever.chunks)} transcript chunks.")
    yield
    logger.info("Shutting down The Lenny Growth Assistant API...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Full-stack AI assistant grounded in Lenny's Podcast transcripts. "
        "Answers product & growth questions, writes Ship 30 for 30 essays, and generates interactive artifacts."
    ),
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permits localhost:3000, localhost:5173, etc.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return {
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "api_status": "active"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
