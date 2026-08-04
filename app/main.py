from fastapi import FastAPI
from config.settings import settings

app = FastAPI(
    title="AI Multi-Agent Developer Assistant",
    version="0.1.0",
    description="Multi-agent AI system for development tasks"
)

@app.get("/")
def root():
    return {
        "project": "AI Multi-Agent Developer Assistant",
        "version": "0.1.0",
        "status": "running",
        "env": settings.APP_ENV
    }

@app.get("/health")
def health_check():
    keys = settings.validate_keys()
    return {
        "status": "healthy",
        "api_keys": keys
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.APP_PORT)