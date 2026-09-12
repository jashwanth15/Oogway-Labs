import pytest
import pytest_asyncio
import httpx
from backend.app.main import app
from backend.app.db.database import init_db


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    await init_db()


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data
        assert "knowledge_base" in data
        assert data["knowledge_base"]["ready"] is True


@pytest.mark.asyncio
async def test_models_endpoint():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/models")
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert len(data["models"]) >= 2
        # Check providers
        providers = [m["provider"] for m in data["models"]]
        assert "ollama" in providers
        assert "anthropic" in providers


@pytest.mark.asyncio
async def test_session_crud_api():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Create
        create_res = await client.post("/api/sessions", json={"title": "PMF Strategy Session"})
        assert create_res.status_code == 201
        session_data = create_res.json()
        session_id = session_data["id"]

        # Read
        get_res = await client.get(f"/api/sessions/{session_id}")
        assert get_res.status_code == 200
        assert get_res.json()["title"] == "PMF Strategy Session"

        # List
        list_res = await client.get("/api/sessions")
        assert list_res.status_code == 200
        assert any(s["id"] == session_id for s in list_res.json())

        # Delete
        del_res = await client.delete(f"/api/sessions/{session_id}")
        assert del_res.status_code == 204


@pytest.mark.asyncio
async def test_transcript_search_api():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/transcripts/search", json={
            "query": "Elena Verna B2B loops",
            "top_k": 3
        })
        assert res.status_code == 200
        data = res.json()
        assert data["total_found"] > 0
        assert len(data["results"]) > 0
