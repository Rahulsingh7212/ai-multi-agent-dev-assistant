from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.callbacks import AsyncCallbackHandler
from config.settings import settings
from typing import List, Optional, AsyncIterator
import logging

logger = logging.getLogger(__name__)


class LLMService:
    """
    Service layer for LLM interactions.
    Wraps LangChain + Gemini with configuration.
    """

    def __init__(self):
        self._llm = None
        self._streaming_llm = None
        self._initialize_llm()

    def _initialize_llm(self):
        """Initialize LLM instances (normal + streaming)"""
        try:
            # Normal LLM (for non-streaming responses)
            self._llm = ChatGoogleGenerativeAI(
                model=settings.LLM_MODEL,
                google_api_key=settings.GEMINI_API_KEY,
                temperature=settings.LLM_TEMPERATURE,
                max_output_tokens=settings.LLM_MAX_TOKENS,
            )

            # Streaming LLM (for SSE responses)
            self._streaming_llm = ChatGoogleGenerativeAI(
                model=settings.LLM_MODEL,
                google_api_key=settings.GEMINI_API_KEY,
                temperature=settings.LLM_TEMPERATURE,
                max_output_tokens=settings.LLM_MAX_TOKENS,
                streaming=True,
            )

            logger.info(f"✅ LLM initialized: {settings.LLM_MODEL}")

        except Exception as e:
            logger.error(f"❌ LLM initialization failed: {e}")
            raise

    @property
    def model_name(self) -> str:
        return settings.LLM_MODEL

    def chat(self, message: str) -> str:
        """
        Synchronous chat — returns full response string.
        """
        try:
            system_prompt = SystemMessage(
                content=(
                    "You are an expert AI Developer Assistant. "
                    "You help with coding, debugging, architecture, "
                    "and software development best practices. "
                    "Be concise, accurate, and provide code examples when helpful."
                )
            )
            human_message = HumanMessage(content=message)

            response = self._llm.invoke([system_prompt, human_message])

            content = response.content

            # Latest LangChain may return list instead of string
            if isinstance(content, list):
                text_parts = []

                for item in content:
                    if isinstance(item, str):
                        text_parts.append(item)
                    elif isinstance(item, dict):
                        if "text" in item:
                            text_parts.append(item["text"])

                content = "\n".join(text_parts)

            logger.info(f"💬 Chat response generated ({len(content)} chars)")
            return content

        except Exception as e:
            logger.error(f"❌ Chat error: {e}")
            raise

    async def chat_stream(self, message: str) -> AsyncIterator[str]:
        """
        Asynchronous streaming chat — yields chunks for SSE.
        """
        try:
            system_prompt = SystemMessage(
                content=(
                    "You are an expert AI Developer Assistant. "
                    "You help with coding, debugging, architecture, "
                    "and software development best practices. "
                    "Be concise, accurate, and provide code examples when helpful."
                )
            )
            human_message = HumanMessage(content=message)

            async for chunk in self._streaming_llm.astream(
                [system_prompt, human_message]
            ):
                content = chunk.content
                
                # String
                if isinstance(content, str):
                    yield content

                # Latest LangChain returns list
                elif isinstance(content, list):
                    text = ""

                    for item in content:
                        if isinstance(item, str):
                            text += item

                        elif isinstance(item, dict):
                            if item.get("type") == "text":
                                text += item.get("text", "")

                    if text:
                        yield text

            logger.info("💬 Streaming chat response completed")

        except Exception as e:
            logger.error(f"❌ Streaming chat error: {e}")
            raise


# ============================
# Singleton instance
# ============================
llm_service = LLMService()