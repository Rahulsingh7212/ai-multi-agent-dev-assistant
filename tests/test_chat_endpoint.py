"""
Automated tests for Stage 1 chat endpoint.
Run: pytest tests/test_chat_endpoint.py -v
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ============================
# System Tests
# ============================

@pytest.mark.anyio
async def test_root_endpoint(client):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["project"] == "AI Multi-Agent Developer Assistant"
    assert data["status"] == "running"


@pytest.mark.anyio
async def test_health_endpoint(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "model" in data


# ============================
# Chat Tests
# ============================

@pytest.mark.anyio
async def test_chat_normal(client):
    response = await client.post(
        "/api/v1/chat",
        json={
            "message": "Say hello in one word",
            "stream": False
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert len(data["reply"]) > 0
    assert data["model"] == "gemini-3.5-flash"


@pytest.mark.anyio
async def test_chat_with_session_id(client):
    response = await client.post(
        "/api/v1/chat",
        json={
            "message": "What is 2+2?",
            "session_id": "test-session-001",
            "stream": False
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "test-session-001"


@pytest.mark.anyio
async def test_chat_empty_message_validation(client):
    response = await client.post(
        "/api/v1/chat",
        json={"message": "", "stream": False}
    )
    assert response.status_code == 422  # Validation error


@pytest.mark.anyio
async def test_chat_missing_message_field(client):
    response = await client.post(
        "/api/v1/chat",
        json={"stream": False}
    )
    assert response.status_code == 422  # Validation error