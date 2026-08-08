import logging

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
from app.routes.rag import router as rag_router
from app.routes.agent import router as agent_router
from app.routes.monitoring import router as monitoring_router    # 🆕 NEW
from app.middleware.error_handler import (
    ErrorHandlerMiddleware,
    RequestLoggingMiddleware,
    RateLimitMiddleware,
)


logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version="0.6.0",  # Stage 5
    description=(
        "🤖 AI Multi-Agent Developer Assistant\n\n"
        "Stage 5: Persistent Memory + Tool Registry\n\n"
        "Features:\n"
        "- Redis-backed conversation memory\n"
        "- Per-user memory isolation\n"
        "- Central tool registry (19 tools, 5 agents)\n"
        "- Retry logic with exponential backoff\n"
        "- Error handling middleware\n"
        "- Request logging & rate limiting\n"
    ),
)

# ============================
# MIDDLEWARE (order matters!)
# ============================

# 1. Error handler (outermost — catches everything)
app.add_middleware(ErrorHandlerMiddleware)

# 2. Request logging
app.add_middleware(RequestLoggingMiddleware)

# 3. Rate limiting
app.add_middleware(RateLimitMiddleware, max_requests=60, window_seconds=60)

# 4. CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================
# REGISTER ROUTES
# ============================
app.include_router(system_router)
app.include_router(chat_router)
app.include_router(rag_router)
app.include_router(agent_router)
app.include_router(monitoring_router)          # 🆕 NEW

logger.info(f"🚀 {settings.APP_NAME} v0.6.0 starting...")


@app.on_event("startup")
async def startup_event():
    # Register all tools
    from app.tools.register_all import register_all_tools
    register_all_tools()

    logger.info("✅ Application startup complete")
    logger.info(f"🎯 Supervisor: 5 agents (code, resume, pdf, github, web)")
    logger.info(f"🧠 Memory backend: {settings.MEMORY_BACKEND}")
    logger.info(f"🔧 Tool registry: initialized")

    if settings.is_redis_ready():
        logger.info("✅ Redis: connected")
    else:
        logger.warning("⚠️  Redis: disconnected — using in-memory fallback")

    if not settings.is_ready():
        logger.warning("⚠️  GEMINI_API_KEY is missing!")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("👋 Application shutting down")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.APP_PORT, reload=True)