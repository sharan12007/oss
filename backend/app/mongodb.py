"""MongoDB connection module for user authentication."""

import logging
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import get_settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None
_db = None


async def get_mongo_client() -> AsyncIOMotorClient:
    """Get or create the MongoDB async client."""
    global _client
    if _client is None:
        settings = get_settings()
        _client = AsyncIOMotorClient(settings.mongodb_uri)
        logger.info(f"✅ Connected to MongoDB at {settings.mongodb_uri}")
    return _client


async def get_mongo_db():
    """Get the GeneGraph MongoDB database."""
    global _db
    if _db is None:
        client = await get_mongo_client()
        settings = get_settings()
        _db = client[settings.mongodb_db_name]
    return _db


async def get_users_collection():
    """Get the users collection."""
    db = await get_mongo_db()
    return db["users"]


async def get_reset_tokens_collection():
    """Get the password reset tokens collection."""
    db = await get_mongo_db()
    return db["reset_tokens"]


async def setup_mongodb_indexes():
    """Create indexes for users collection."""
    users = await get_users_collection()
    await users.create_index("email", unique=True)
    await users.create_index("username", unique=True)
    
    reset_tokens = await get_reset_tokens_collection()
    await reset_tokens.create_index("token", unique=True)
    await reset_tokens.create_index("expires_at", expireAfterSeconds=0)
    
    logger.info("✅ MongoDB indexes created")


async def close_mongo_client():
    """Close the MongoDB client."""
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
        logger.info("MongoDB connection closed")
