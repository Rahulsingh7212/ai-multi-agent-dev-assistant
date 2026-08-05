import logging

# ============================
# Logging Setup
# ============================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.settings import settings
from app.routes.chat import router as chat_router
from app.routes.system import router as system_router
from app.routes.rag import router as rag_router        # 🆕 NEW
from app.routes.agent import router as agent_router          # 🆕 NEW


logger = logging.getLogger(__name__)

# ============================
# FastAPI App
# ============================
app = FastAPI(
    title=settings.APP_NAME,
    version="0.4.0",  # Updated for Stage 2
    description=(
    "🤖 AI Multi-Agent Developer Assistant\n\n"
    "Stage 3: Code Agent with LangGraph + Tools + Memory\n\n"
    "Endpoints:\n"
    "- POST /api/v1/agent/code   — Run Code Agent\n"
    "- GET  /api/v1/agent/sessions — List sessions\n"
    "- GET  /api/v1/agent/session/{id} — Get session history\n"
    "- DELETE /api/v1/agent/session/{id} — Clear session\n"
    "- POST /api/v1/chat         — Simple chat\n"
    "- POST /api/v1/ingest       — Ingest documents\n"
    "- POST /api/v1/rag-query    — RAG Q&A\n"
    "- GET  /health              — Health check\n"
    ), 
)

# ============================
# CORS Middleware
# ============================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================
# Register Routers
# ============================
app.include_router(system_router)
app.include_router(chat_router)
app.include_router(rag_router)          # 🆕 NEW
app.include_router(agent_router)        # 🆕 NEW
logger.info(f"🚀 {settings.APP_NAME} v0.4.0 starting...")
logger.info(f"🤖 LLM Model: {settings.LLM_MODEL}")


@app.on_event("startup")
async def startup_event():
    logger.info("✅ Application startup complete")
    logger.info("🤖 Code Agent: 4 tools (generate, debug, explain, execute)")
    logger.info("🧠 Conversation memory: active")

    if not settings.is_ready():
        logger.warning("⚠️ GEMINI_API_KEY is missing!")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("👋 Application shutting down")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.APP_PORT, reload=True)