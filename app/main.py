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

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version="0.5.0",  # Stage 4
    description=(
        "🤖 AI Multi-Agent Developer Assistant\n\n"
        "Stage 4: Multi-Agent Supervisor with 5 Specialist Agents\n\n"
        "Agents:\n"
        "- 🧑‍💻 Code Agent: Generate, debug, explain, execute code\n"
        "- 📄 Resume Agent: Parse, analyze, improve resumes\n"
        "- 📑 PDF Agent: Document Q&A, summarize, compare\n"
        "- 🐙 GitHub Agent: Search repos, issues, PRs\n"
        "- 🌐 Web Agent: Search, real-time info, news\n\n"
        "Main Endpoint:\n"
        "- POST /api/v1/agent/run — Supervisor auto-routes to best agent\n"
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system_router)
app.include_router(chat_router)
app.include_router(rag_router)
app.include_router(agent_router)

logger.info(f"🚀 {settings.APP_NAME} v0.5.0 starting...")


@app.on_event("startup")
async def startup_event():
    logger.info("✅ Application startup complete")
    logger.info("🎯 Supervisor: 5 agents (code, resume, pdf, github, web)")
    logger.info("🧠 Conversation memory: active")
    if not settings.is_ready():
        logger.warning("⚠️  GEMINI_API_KEY is missing!")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("👋 Application shutting down")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.APP_PORT, reload=True)