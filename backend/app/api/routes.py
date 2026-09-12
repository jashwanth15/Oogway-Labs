import json
import logging
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, desc
from sqlalchemy.orm import selectinload

from backend.app.config import settings
from backend.app.db.database import get_db
from backend.app.db.models import SessionModel, MessageModel, ArtifactModel
from backend.app.schemas.chat import (
    ChatRequest,
    ChatMessageResponse,
    ArtifactResponse,
    SearchQuery,
    SearchResponse,
)
from backend.app.schemas.session import (
    SessionCreate,
    SessionUpdate,
    SessionResponse,
    SessionDetailResponse,
)
from backend.app.api.health import get_system_health
from backend.app.services.agent import GrowthAgent
from backend.app.services.retrieval import HybridRetriever

logger = logging.getLogger(__name__)
router = APIRouter()
agent = GrowthAgent()


@router.get("/health")
async def health_check():
    """Health diagnostic endpoint for evaluator."""
    return await get_system_health()


@router.get("/models")
async def list_models():
    """Lists available local Ollama models and configured cloud LLMs."""
    ollama_info = await agent.check_ollama_status()
    models = []

    # Local Ollama Models
    if ollama_info.get("available"):
        for m in ollama_info.get("models", []):
            models.append({
                "id": f"ollama:{m}",
                "name": f"Local: {m} (Ollama)",
                "provider": "ollama",
                "is_local": True,
                "is_active": m == settings.DEFAULT_LOCAL_MODEL
            })
    else:
        models.append({
            "id": f"ollama:{settings.DEFAULT_LOCAL_MODEL}",
            "name": f"Local: {settings.DEFAULT_LOCAL_MODEL} (Offline)",
            "provider": "ollama",
            "is_local": True,
            "is_active": False
        })

    # Free High-Performance Cloud Models
    models.append({
        "id": "gemini:gemini-2.5-flash",
        "name": "Cloud: Gemini 2.5 Flash (Google - Free)",
        "provider": "google",
        "is_local": False,
        "is_active": bool(settings.GEMINI_API_KEY)
    })
    models.append({
        "id": "groq:openai/gpt-oss-120b",
        "name": "Cloud: GPT-OSS 120B (Groq - Free & Fast)",
        "provider": "groq",
        "is_local": False,
        "is_active": bool(settings.GROQ_API_KEY)
    })

    # Standard Cloud Models
    models.append({
        "id": "claude-3-5-sonnet",
        "name": "Cloud: Claude 3.5 Sonnet (Anthropic)",
        "provider": "anthropic",
        "is_local": False,
        "is_active": bool(settings.ANTHROPIC_API_KEY)
    })
    models.append({
        "id": "gpt-4o",
        "name": "Cloud: GPT-4o (OpenAI)",
        "provider": "openai",
        "is_local": False,
        "is_active": bool(settings.OPENAI_API_KEY)
    })

    return {
        "models": models,
        "default": f"ollama:{settings.DEFAULT_LOCAL_MODEL}" if ollama_info.get("available") else "ollama:mistral:latest"
    }


# ================= SESSIONS CRUD =================

@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(payload: SessionCreate, db: AsyncSession = Depends(get_db)):
    """Creates a new conversation session."""
    new_session = SessionModel(
        title=payload.title or "New Growth Conversation",
        model_used=payload.model_used or settings.DEFAULT_LOCAL_MODEL,
        meta_info=payload.meta_info or {}
    )
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    return new_session


@router.get("/sessions", response_model=List[SessionResponse])
async def list_sessions(db: AsyncSession = Depends(get_db)):
    """Lists all past sessions ordered by most recent."""
    stmt = select(SessionModel).order_by(desc(SessionModel.updated_at))
    result = await db.execute(stmt)
    sessions = result.scalars().all()
    return sessions


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves full session history with messages and generated artifacts."""
    stmt = (
        select(SessionModel)
        .where(SessionModel.id == session_id)
        .options(
            selectinload(SessionModel.messages).selectinload(MessageModel.artifacts),
            selectinload(SessionModel.artifacts)
        )
    )
    result = await db.execute(stmt)
    session = result.scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Deletes a session and associated history."""
    stmt = delete(SessionModel).where(SessionModel.id == session_id)
    result = await db.execute(stmt)
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Session not found")
    await db.commit()
    return None


# ================= CHAT & ARTIFACTS =================

@router.post("/chat")
async def chat_stream(payload: ChatRequest, db: AsyncSession = Depends(get_db)):
    """
    Main SSE Streaming Endpoint:
    Streams thinking status, grounded citations, tokens, and artifacts in real-time.
    Persists user input and assistant response to PostgreSQL/SQLite.
    """
    session_id = payload.session_id

    # Create session if none provided
    if not session_id:
        title = payload.message[:35] + ("..." if len(payload.message) > 35 else "")
        new_session = SessionModel(
            title=title,
            model_used=payload.model or settings.DEFAULT_LOCAL_MODEL
        )
        db.add(new_session)
        await db.commit()
        await db.refresh(new_session)
        session_id = new_session.id
    else:
        # Verify session exists
        stmt = select(SessionModel).where(SessionModel.id == session_id)
        res = await db.execute(stmt)
        session = res.scalars().first()
        if not session:
            session = SessionModel(
                id=session_id,
                title=payload.message[:35] + ("..." if len(payload.message) > 35 else ""),
                model_used=payload.model or settings.DEFAULT_LOCAL_MODEL
            )
            db.add(session)
            await db.commit()

    # Save user message
    user_msg = MessageModel(
        session_id=session_id,
        role="user",
        content=payload.message
    )
    db.add(user_msg)
    await db.commit()
    await db.refresh(user_msg)

    # Fetch conversation history for context
    hist_stmt = (
        select(MessageModel)
        .where(MessageModel.session_id == session_id)
        .order_by(MessageModel.created_at)
    )
    hist_res = await db.execute(hist_stmt)
    history_messages = [{"role": m.role, "content": m.content} for m in hist_res.scalars().all()]

    async def event_generator():
        # Emit session metadata first
        yield f"data: {json.dumps({'type': 'session_init', 'session_id': session_id})}\n\n"

        assistant_full_text = ""
        resolved_citations = []
        resolved_artifacts = []

        try:
            async for event in agent.stream_chat(
                message=payload.message,
                history=history_messages[:-1],  # Exclude current user prompt as it's passed separately
                model_name=payload.model,
                skill=payload.skill
            ):
                if event.get("type") == "citations":
                    resolved_citations = event.get("citations", [])
                elif event.get("type") == "token":
                    assistant_full_text += event.get("token", "")
                elif event.get("type") == "done":
                    assistant_full_text = event.get("full_text", assistant_full_text)
                    resolved_artifacts = event.get("artifacts", [])

                yield f"data: {json.dumps(event)}\n\n"

        except Exception as e:
            logger.error(f"Error in chat stream: {e}")
            err_data = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(err_data)}\n\n"

        # Persist assistant response & artifacts after streaming completes
        try:
            from backend.app.db.database import AsyncSessionLocal
            async with AsyncSessionLocal() as save_db:
                asst_msg = MessageModel(
                    session_id=session_id,
                    role="assistant",
                    content=assistant_full_text,
                    citations=resolved_citations
                )
                save_db.add(asst_msg)
                await save_db.commit()
                await save_db.refresh(asst_msg)

                for art in resolved_artifacts:
                    art_obj = ArtifactModel(
                        session_id=session_id,
                        message_id=asst_msg.id,
                        title=art.get("title", "Untitled Artifact"),
                        artifact_type=art.get("artifact_type", "markdown"),
                        content=art.get("content", "")
                    )
                    save_db.add(art_obj)
                await save_db.commit()
        except Exception as e:
            logger.error(f"Failed to persist assistant message to DB: {e}")

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/artifacts/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(artifact_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves an individual artifact by ID."""
    stmt = select(ArtifactModel).where(ArtifactModel.id == artifact_id)
    res = await db.execute(stmt)
    artifact = res.scalars().first()
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact


@router.post("/transcripts/search", response_model=SearchResponse)
async def direct_search(payload: SearchQuery):
    """Direct search query against transcript database."""
    retriever = HybridRetriever.get_instance()
    citations, _ = retriever.search(
        query=payload.query,
        top_k=payload.top_k,
        guest_filter=payload.guest_filter
    )
    return SearchResponse(
        query=payload.query,
        results=citations,
        total_found=len(citations)
    )
