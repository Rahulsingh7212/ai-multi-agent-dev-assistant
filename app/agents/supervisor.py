from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from app.agents.state import AgentState
from config.settings import settings

import json
import re
import logging

logger = logging.getLogger(__name__)


class Supervisor:
    """
    Supervisor Agent — router of the multi-agent system.

    Responsibilities:
    1. Analyze user query
    2. Route automatically when no agent is selected
    3. Respect user's manually selected agent
    4. Handle uploaded resume/PDF files
    """

    AVAILABLE_AGENTS = {
        "code_agent": {
            "description": "Code generation, debugging, explanation, execution in any language",
            "keywords": [
                "code",
                "function",
                "debug",
                "fix bug",
                "explain code",
                "run code",
                "write",
                "implement",
                "refactor",
                "python",
                "javascript",
                "api endpoint",
                "algorithm",
                "script",
                "program",
                "syntax error",
                "compile",
            ],
        },

        "resume_agent": {
            "description": "Resume/CV parsing, analysis, and improvement",
            "keywords": [
                "resume",
                "cv",
                "curriculum",
                "job application",
                "cover letter",
                "ats",
                "hiring",
                "career",
                "skills gap",
                "interview",
            ],
        },

        "pdf_agent": {
            "description": "Document Q&A, summarization, and comparison",
            "keywords": [
                "document",
                "pdf",
                "summarize document",
                "what does the doc say",
                "compare documents",
                "read file",
                "upload",
            ],
        },

        "github_agent": {
            "description": "GitHub repository search, issues, and pull requests",
            "keywords": [
                "github",
                "repo",
                "repository",
                "issues",
                "pull request",
                "pr",
                "open source",
                "fork",
                "star",
                "commit",
                "branch",
                "contributor",
            ],
        },

        "web_agent": {
            "description": "Web search, real-time information, and latest news",
            "keywords": [
                "search",
                "latest",
                "news",
                "current",
                "trending",
                "what is",
                "who is",
                "when did",
                "recent",
                "today",
                "real-time",
                "lookup",
                "find information",
                "google",
            ],
        },
    }

    def __init__(self):
        self.llm = ChatGroq(
            model=settings.LLM_MODEL,
            api_key=settings.GROQ_API_KEY,
            temperature=0.1,
            max_tokens=512,
        )

        logger.info(
            "✅ Supervisor initialized with 5 agents"
        )

    def route(self, state: AgentState) -> AgentState:
        """
        Supervisor routing node.

        Priority:
        1. User-selected agent
        2. Uploaded file detection
        3. LLM automatic routing
        4. Safe code_agent fallback
        """

        user_query = state["user_query"]

        # ============================================================
        # 1. USER SELECTED AGENT
        # ============================================================

        selected_agent = state.get("selected_agent")

        if selected_agent:
            # Normalize values coming from frontend
            selected_agent = selected_agent.strip().lower()

            # Allow friendly names too
            agent_aliases = {
                "supervisor": None,
                "code agent": "code_agent",
                "resume agent": "resume_agent",
                "pdf agent": "pdf_agent",
                "github agent": "github_agent",
                "web agent": "web_agent",
            }

            if selected_agent in agent_aliases:
                selected_agent = agent_aliases[selected_agent]

            # If a valid specific agent was selected,
            # bypass LLM routing completely.
            if selected_agent in self.AVAILABLE_AGENTS:

                logger.info(
                    f"🎯 User selected agent → {selected_agent}"
                )

                return {
                    **state,
                    "next_agent": selected_agent,
                    "supervisor_reasoning": (
                        f"User manually selected {selected_agent}"
                    ),
                    "agent_handoff": False,
                    "messages": [
                        AIMessage(
                            content=(
                                f"[Supervisor] → {selected_agent} "
                                f"(user selected)"
                            )
                        )
                    ],
                }

            # If user selected "supervisor", continue
            # with automatic routing.

        # ============================================================
        # 2. FILE UPLOAD DETECTION
        # ============================================================

        has_file = bool(
            state.get("uploaded_file_path")
        )

        file_path = state.get(
            "uploaded_file_path",
            ""
        )

        logger.info(
            f"🎯 Supervisor routing: "
            f"{user_query[:80]}..."
        )

        if has_file:

            file_ext = (
                file_path.rsplit(".", 1)[-1].lower()
                if "." in file_path
                else ""
            )

            if file_ext == "pdf":

                content_preview = (
                    state.get(
                        "uploaded_file_content"
                    )
                    or ""
                )[:500].lower()

                resume_indicators = [
                    "experience",
                    "education",
                    "skills",
                    "objective",
                    "summary",
                    "work history",
                    "employment",
                    "curriculum",
                ]

                if any(
                    indicator in content_preview
                    for indicator in resume_indicators
                ):

                    logger.info(
                        "🎯 File detected as resume → resume_agent"
                    )

                    return {
                        **state,
                        "next_agent": "resume_agent",
                        "supervisor_reasoning": (
                            "Uploaded PDF detected as resume "
                            "based on content keywords"
                        ),
                        "agent_handoff": False,
                        "messages": [
                            AIMessage(
                                content=(
                                    "[Supervisor] → resume_agent "
                                    "(resume file detected)"
                                )
                            )
                        ],
                    }

                logger.info(
                    "🎯 File detected as document → pdf_agent"
                )

                return {
                    **state,
                    "next_agent": "pdf_agent",
                    "supervisor_reasoning": (
                        "Uploaded PDF detected as general document"
                    ),
                    "agent_handoff": False,
                    "messages": [
                        AIMessage(
                            content=(
                                "[Supervisor] → pdf_agent "
                                "(document file detected)"
                            )
                        )
                    ],
                }

        # ============================================================
        # 3. LLM AUTOMATIC ROUTING
        # ============================================================

        agent_descriptions = "\n".join(
            [
                f"- {name}: {info['description']}"
                for name, info in self.AVAILABLE_AGENTS.items()
            ]
        )

        routing_prompt = f"""
You are a Supervisor Agent that routes user requests
to the appropriate specialist agent.

AVAILABLE AGENTS:

{agent_descriptions}

USER REQUEST:
{user_query}

Analyze the request and determine which agent should handle it.

Choose based on the PRIMARY intent.

Respond with JSON ONLY:

{{
    "next_agent": "agent_name_here",
    "reasoning": "brief explanation of why this agent"
}}

The next_agent MUST be one of:

code_agent
resume_agent
pdf_agent
github_agent
web_agent
"""

        try:

            response = self.llm.invoke(
                [
                    SystemMessage(
                        content=routing_prompt
                    ),
                    HumanMessage(
                        content=user_query
                    ),
                ]
            )

            # ========================================================
            # Normalize Groq/LangChain response content
            # ========================================================

            content = response.content

            if isinstance(content, list):

                text_parts = []

                for block in content:

                    if isinstance(block, dict):

                        text = block.get(
                            "text"
                        )

                        if text:
                            text_parts.append(text)

                    elif isinstance(block, str):

                        text_parts.append(block)

                content = "".join(text_parts)

            if not isinstance(content, str):

                content = str(content)

            # IMPORTANT:
            # Parse normalized content, not response.content
            parsed = self._parse_json(content)

            next_agent = parsed.get(
                "next_agent",
                "code_agent"
            )

            reasoning = parsed.get(
                "reasoning",
                ""
            )

            # ========================================================
            # Validate selected agent
            # ========================================================

            if next_agent not in self.AVAILABLE_AGENTS:

                logger.warning(
                    f"⚠️ Invalid agent returned by LLM: "
                    f"{next_agent}"
                )

                next_agent = "code_agent"

                reasoning = (
                    f"Invalid agent fallback. "
                    f"Original reasoning: {reasoning}"
                )

            logger.info(
                f"🎯 Supervisor → {next_agent} | "
                f"{reasoning}"
            )

            return {
                **state,
                "next_agent": next_agent,
                "supervisor_reasoning": reasoning,
                "agent_handoff": False,
                "messages": [
                    AIMessage(
                        content=(
                            f"[Supervisor] → {next_agent} | "
                            f"{reasoning}"
                        )
                    )
                ],
            }

        except Exception as e:

            logger.error(
                f"❌ Supervisor routing error: {e}"
            )

            return {
                **state,
                "next_agent": "code_agent",
                "supervisor_reasoning": (
                    f"Fallback due to error: {str(e)}"
                ),
                "agent_handoff": False,
                "error": str(e),
                "messages": [
                    AIMessage(
                        content=(
                            "[Supervisor] → code_agent "
                            "(fallback)"
                        )
                    )
                ],
            }

    def _parse_json(
        self,
        text: str
    ) -> dict:
        """
        Parse JSON safely from an LLM response.
        """

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

        # Remove markdown code fences
        text = re.sub(
            r"```json\s*",
            "",
            text,
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"```\s*",
            "",
            text,
        )

        text = text.strip()

        try:

            return json.loads(text)

        except json.JSONDecodeError:

            # Try to extract the first JSON object
            match = re.search(
                r"\{.*\}",
                text,
                re.DOTALL,
            )

            if match:

                return json.loads(
                    match.group()
                )

            raise ValueError(
                "Could not parse JSON from "
                f"LLM response: {text}"
            )


# ============================================================
# Singleton
# ============================================================

supervisor = Supervisor()