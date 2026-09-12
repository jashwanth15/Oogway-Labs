import logging
from typing import Dict, Any
from sqlalchemy import text
from backend.app.db.database import AsyncSessionLocal, engine
from backend.app.services.retrieval import HybridRetriever
from backend.app.services.agent import GrowthAgent

logger = logging.getLogger(__name__)


async def get_system_health() -> Dict[str, Any]:
    """Diagnoses DB, Ollama, and Knowledge Base index health."""
    status = {
        "status": "healthy",
        "database": {"connected": False, "type": "unknown"},
        "ollama": {"available": False, "models": []},
        "knowledge_base": {"ready": False, "total_chunks": 0},
    }

    # 1. Check Database
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            status["database"]["connected"] = True
            status["database"]["type"] = engine.dialect.name
    except Exception as e:
        logger.warning(f"Health DB check failed: {e}")
        status["database"]["connected"] = False
        status["database"]["error"] = str(e)
        status["status"] = "degraded"

    # 2. Check Ollama
    agent = GrowthAgent()
    ollama_info = await agent.check_ollama_status()
    status["ollama"] = ollama_info
    if not ollama_info["available"]:
        status["status"] = "degraded" if status["status"] == "healthy" else status["status"]

    # 3. Check Retriever / Knowledge Base
    retriever = HybridRetriever.get_instance()
    status["knowledge_base"]["ready"] = retriever.is_ready
    status["knowledge_base"]["total_chunks"] = len(retriever.chunks)

    return status
