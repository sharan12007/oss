"""
GeneGraph — AI-Powered Gene-Disease-Protein Knowledge Graph Explorer
Main FastAPI application entry point.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database import get_driver, close_driver
from app.schema import setup_schema
from app.mongodb import setup_mongodb_indexes, close_mongo_client
from app.routes import graph, ai, ingest
from app.routes.auth import router as auth_router
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    logger.info("🧬 GeneGraph starting up...")
    try:
        await get_driver()
        logger.info("✅ Connected to Neo4j")
        await setup_schema()
        logger.info("✅ Schema initialized")
    except Exception as e:
        logger.error(f"❌ Neo4j startup error: {e}")
        logger.info("⚠️  App will start but DB features may not work. Check your .env file.")

    try:
        await setup_mongodb_indexes()
        logger.info("✅ MongoDB ready")
    except Exception as e:
        logger.error(f"❌ MongoDB startup error: {e}")
        logger.info("⚠️  Auth features may not work. Check your MongoDB connection.")

    yield

    logger.info("🧬 GeneGraph shutting down...")
    await close_driver()
    await close_mongo_client()


app = FastAPI(
    title="GeneGraph API",
    description="AI-powered gene-disease-protein knowledge graph explorer",
    version="0.1.0",
    lifespan=lifespan,
)

# ─── CORS ─────────────────────────────────────────────────────────────────────

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routes ───────────────────────────────────────────────────────────────────

app.include_router(auth_router, tags=["Auth"])
app.include_router(graph.router, tags=["Graph"])
app.include_router(ai.router, tags=["AI"])
app.include_router(ingest.router, tags=["Ingestion"])


@app.get("/")
async def root():
    return {
        "name": "GeneGraph API",
        "version": "0.1.0",
        "description": "AI-powered gene-disease-protein knowledge graph explorer",
        "disclaimer": "⚠️ For research use only. Not medical advice.",
    }


@app.get("/health")
async def health():
    try:
        driver = await get_driver()
        await driver.verify_connectivity()
        return {"status": "healthy", "neo4j": "connected"}
    except Exception as e:
        return {"status": "degraded", "neo4j": str(e)}
