from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from app.agents.state import AgentState
from config.settings import settings
import json
import re
import logging

logger = logging.getLogger(__name__)


class Supervisor:
    """
    Supervisor Agent — the router of the multi-agent system.

    Responsibilities:
    1. Analyze the user's query
    2. Classify the intent
    3. Route to the appropriate specialist agent

    Available agents:
    - code_agent:    Code generation, debugging, explanation, execution
    - resume_agent:  Resume parsing, analysis, improvement
    - pdf_agent:     Document Q&A, summarization, comparison
    - github_agent:  GitHub repos, issues, PRs
    - web_agent:     Web search, real-time information, news
    """

    AVAILABLE_AGENTS = {
        "code_agent": {
            "description": "Code generation, debugging, explanation, execution in any language",
            "keywords": ["code", "function", "debug", "fix bug", "explain code", "run code",
                        "write", "implement", "refactor", "python", "javascript", "api endpoint",
                        "algorithm", "script", "program", "syntax error", "compile"],
        },
        "resume_agent": {
            "description": "Resume/CV parsing, analysis, and improvement",
            "keywords": ["resume", "cv", "curriculum", "job application", "cover letter",
                        "ats", "hiring", "career", "skills gap", "interview"],
        },
        "pdf_agent": {
            "description": "Document Q&A, summarization, and comparison",
            "keywords": ["document", "pdf", "summarize document", "what does the doc say",
                        "compare documents", "read file", "upload"],
        },
        "github_agent": {
            "description": "GitHub repository search, issues, and pull requests",
            "keywords": ["github", "repo", "repository", "issues", "pull request", "pr",
                        "open source", "fork", "star", "commit", "branch", "contributor"],
        },
        "web_agent": {
            "description": "Web search, real-time information, and latest news",
            "keywords": ["search", "latest", "news", "current", "trending", "what is",
                        "who is", "when did", "recent", "today", "real-time", "lookup",
                        "find information", "google"],
        },
    }

    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=settings.LLM_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.1,  # Very low temperature for consistent routing
            max_output_tokens=512,
        )
        logger.info("✅ Supervisor initialized with 5 agents")

    def route(self, state: AgentState) -> AgentState:
        """
        Supervisor routing node.
        Analyzes query and decides which agent should handle it.
        """
        user_query = state["user_query"]

        # Check if a file was uploaded (likely resume or PDF)
        has_file = bool(state.get("uploaded_file_path"))
        file_path = state.get("uploaded_file_path", "")

        logger.info(f"🎯 Supervisor routing: {user_query[:80]}...")

        # Quick heuristic check for file uploads
        if has_file:
            file_ext = file_path.rsplit(".", 1)[-1].lower() if "." in file_path else ""
            if file_ext == "pdf":
                # Check if it looks like a resume
                content_preview = (state.get("uploaded_file_content") or "")[:500].lower()
                resume_indicators = ["experience", "education", "skills", "objective",
                                    "summary", "work history", "employment", "curriculum"]
                if any(ind in content_preview for ind in resume_indicators):
                    logger.info("🎯 File detected as resume → resume_agent")
                    return {
                        **state,
                        "next_agent": "resume_agent",
                        "supervisor_reasoning": "Uploaded PDF detected as resume based on content keywords",
                        "messages": [AIMessage(content="[Supervisor] → resume_agent (resume file detected)")],
                    }
                else:
                    logger.info("🎯 File detected as document → pdf_agent")
                    return {
                        **state,
                        "next_agent": "pdf_agent",
                        "supervisor_reasoning": "Uploaded PDF detected as general document",
                        "messages": [AIMessage(content="[Supervisor] → pdf_agent (document file detected)")],
                    }

        # LLM-based routing for text queries
        agent_descriptions = "\n".join([
            f"- {name}: {info['description']}"
            for name, info in self.AVAILABLE_AGENTS.items()
        ])

        routing_prompt = f"""You are a Supervisor Agent that routes user requests to the appropriate specialist agent.

AVAILABLE AGENTS:
{agent_descriptions}

USER REQUEST: {user_query}

Analyze the request and determine which agent should handle it.
Consider the primary intent of the request.

Respond with JSON ONLY:
{{
    "next_agent": "agent_name_here",
    "reasoning": "brief explanation of why this agent"
}}

The next_agent must be one of: code_agent, resume_agent, pdf_agent, github_agent, web_agent"""

        try:
            response = self.llm.invoke([SystemMessage(content=routing_prompt), HumanMessage(content=user_query),
            ])

            content = response.content

            # Gemini/LangChain can return content as a list of blocks
            if isinstance(content, list):
                text_parts = []

                for block in content:
                    if isinstance(block, dict):
                        text = block.get("text")
                        if text:
                            text_parts.append(text)
                    elif isinstance(block, str):
                        text_parts.append(block)

                content = "".join(text_parts)
            
            parsed = self._parse_json(response.content)

            next_agent = parsed.get("next_agent", "code_agent")
            reasoning = parsed.get("reasoning", "")

            # Validate agent name
            if next_agent not in self.AVAILABLE_AGENTS:
                next_agent = "code_agent"
                reasoning = f"Invalid agent fallback. Original: {reasoning}"

            logger.info(f"🎯 Supervisor → {next_agent} | {reasoning}")

            return {
                **state,
                "next_agent": next_agent,
                "supervisor_reasoning": reasoning,
                "messages": [AIMessage(content=f"[Supervisor] → {next_agent} | {reasoning}")],
            }

        except Exception as e:
            logger.error(f"❌ Supervisor routing error: {e}")
            return {
                **state,
                "next_agent": "code_agent",
                "supervisor_reasoning": f"Fallback due to error: {str(e)}",
                "messages": [AIMessage(content="[Supervisor] → code_agent (fallback)")],
            }

    def _parse_json(self, text: str) -> dict:
        """Parse JSON from Gemini response."""

        if isinstance(text, list):
            parts = []

            for block in text:
                if isinstance(block, dict):
                    value = block.get("text")
                    if value:
                        parts.append(value)
                elif isinstance(block, str):
                    parts.append(block)

            text = "".join(parts)

        if not isinstance(text, str):
            text = str(text)

        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
            if match:
                return json.loads(match.group())
            raise ValueError(f"Could not parse JSON from LLM response: {text}")


# ============================
# Singleton
# ============================
supervisor = Supervisor()