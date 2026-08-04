from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.settings import settings
from app.routes.chat import router as chat_router
from app.routes.system import router as system_router
import logging

# ============================
# Logging Setup
# ============================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

# ============================
# FastAPI App
# ============================
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "🤖 AI Multi-Agent Developer Assistant\n\n"
        "Stage 1: FastAPI + LangChain + Gemini + SSE Streaming\n\n"
        "Endpoints:\n"
        "- POST /api/v1/chat — Chat with AI (normal or streaming)\n"
        "- GET  /health — System health check\n"
        "- GET  /docs — Swagger UI\n"
    ),
)

# ============================
# CORS Middleware
# ============================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================
# Register Routers
# ============================
app.include_router(system_router)
app.include_router(chat_router)

logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} starting...")
logger.info(f"🤖 LLM Model: {settings.LLM_MODEL}")


# ============================
# Startup / Shutdown Events
# ============================
@app.on_event("startup")
async def startup_event():
    logger.info("✅ Application startup complete")
    if not settings.is_ready():
        logger.warning("⚠️  GEMINI_API_KEY is missing — LLM calls will fail!")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("👋 Application shutting down")


# ============================
# Direct Run
# ============================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.APP_PORT,
        reload=True,
    )