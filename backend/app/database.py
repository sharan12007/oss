"""Neo4j database connection manager."""

from neo4j import AsyncGraphDatabase, AsyncDriver
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)

_driver: AsyncDriver | None = None


async def get_driver() -> AsyncDriver:
    """Get or create the Neo4j async driver singleton."""
    global _driver
    if _driver is None:
        settings = get_settings()
        _driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
        # Verify connectivity
        await _driver.verify_connectivity()
        logger.info(f"Connected to Neo4j at {settings.neo4j_uri}")
    return _driver


async def close_driver():
    """Close the Neo4j driver."""
    global _driver
    if _driver is not None:
        await _driver.close()
        _driver = None
        logger.info("Neo4j driver closed")


async def read_query(cypher: str, params: dict | None = None, timeout: float = 30.0) -> list[dict]:
    """Execute a read-only Cypher query and return results as list of dicts."""
    settings = get_settings()
    driver = await get_driver()
    async with driver.session(database=settings.neo4j_database) as session:
        result = await session.run(cypher, parameters=params or {}, timeout=timeout)
        records = await result.data()
        return records


async def write_query(cypher: str, params: dict | None = None) -> list[dict]:
    """Execute a write Cypher query and return results as list of dicts."""
    settings = get_settings()
    driver = await get_driver()
    async with driver.session(database=settings.neo4j_database) as session:
        result = await session.run(cypher, parameters=params or {})
        records = await result.data()
        return records
