"""ReelIQ Backend — Main FastAPI Application"""
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import async_engine, Base
from app.routes import auth, instagram, analysis, insights, lab, strategy, competitor, voiceover

settings = get_settings()
Path(settings.LOCAL_STORAGE_DIR).mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables on startup (dev only — use Alembic in production)."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await async_engine.dispose()


app = FastAPI(
    title="ReelIQ API",
    description="AI-Powered Instagram Reel Analysis & Content Optimization Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=settings.LOCAL_STORAGE_DIR), name="static")

# Register all routes
app.include_router(auth.router)
app.include_router(instagram.router)
app.include_router(analysis.router)
app.include_router(insights.router)
app.include_router(lab.router)
app.include_router(strategy.router)
app.include_router(competitor.router)
app.include_router(voiceover.router)


@app.get("/")
async def root():
    return {
        "name": "ReelIQ API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
