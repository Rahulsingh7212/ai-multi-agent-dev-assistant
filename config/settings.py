from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    # API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
    GITHUB_PAT: str = os.getenv("GITHUB_PAT", "")
    GITHUB_USERNAME: str = os.getenv("GITHUB_USERNAME", "")

    # App Config
    APP_ENV: str = os.getenv("APP_ENV", "development")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))

    # Validation
    def validate_keys(self) -> dict:
        status = {}
        status["gemini"] = "✅" if self.GEMINI_API_KEY else "❌ MISSING"
        status["tavily"] = "✅" if self.TAVILY_API_KEY else "❌ MISSING"
        status["github"] = "✅" if self.GITHUB_PAT else "❌ MISSING"
        return status

settings = Settings()