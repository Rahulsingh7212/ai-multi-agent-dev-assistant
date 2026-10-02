from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.tools import render_text_description

from app.agents.state import AgentState
from app.agents.rag_helper import get_rag_context
from config.settings import settings

from typing import List, Dict, Any
import json
import re
import logging


logger = logging.getLogger(__name__)


class GenericAgent:
    """
    Reusable agent node builder.

    Each agent has:
        router -> tool_executor -> response_generator
    """

    def __init__(
        self,
        name: str,
        tools: List,
        tool_map: Dict[str, Any],
        system_description: str,
        temperature: float = 0.3,
    ):
        self.name = name
        self.tools = tools
        self.tool_map = tool_map
        self.system_description = system_description

        self.tool_descriptions = render_text_description(tools)

        self.llm = ChatGroq(
            model=settings.LLM_MODEL,
            api_key=settings.GROQ_API_KEY,
            temperature=temperature,
            max_tokens=settings.LLM_MAX_TOKENS,
        )

        logger.info(
            f"✅ {name} agent initialized with {len(tools)} tools"
        )

    # ============================================================
    # ROUTE QUERY
    # ============================================================

    def route_query(self, state: AgentState) -> AgentState:
        """
        Analyze user query and select the best tool.
        """

        user_query = state["user_query"]
        iteration = state.get("iteration_count", 0) + 1

        logger.info(
            f"🔀 {self.name} routing (iter {iteration}): "
            f"{user_query[:60]}..."
        )

        # --------------------------------------------------------
        # RAG
        # --------------------------------------------------------

        rag_result = get_rag_context(
            user_query,
            k=3,
        )

        rag_context = rag_result.get("context", "")
        rag_sources = rag_result.get("sources", [])

        # --------------------------------------------------------
        # Uploaded file
        # --------------------------------------------------------

        file_content = state.get(
            "uploaded_file_content",
            "",
        )

        # ============================================================
        # DIRECT RESUME FILE HANDLING
        #
        # If an actual resume file is uploaded and this is the
        # resume agent, skip LLM tool-routing completely.
        # ============================================================

        if self.name == "resume_agent" and file_content:

            logger.info(
                "📄 Uploaded resume detected → "
                "skipping LLM tool routing"
            )

            return {
                **state,
                "agent_type": "resume_agent",
                "tool_name": "resume_parse",
                "tool_input": {
                    "resume_text": file_content,
                },
                "rag_context": rag_context,
                "rag_sources": rag_sources,
                "iteration_count": iteration,
                "messages": [
                    AIMessage(
                        content=(
                            "[resume_agent] → resume_parse "
                            "(uploaded resume)"
                        )
                    )
                ],
            }

        # --------------------------------------------------------
        # File section for normal routing
        # --------------------------------------------------------

        file_section = ""

        if file_content:

            file_section = (
                "\nUPLOADED FILE CONTENT:\n"
                f"{file_content[:3000]}\n\n"
                "Use this content for your analysis."
            )

        # --------------------------------------------------------
        # RAG section
        # --------------------------------------------------------

        rag_section = ""

        if rag_context:

            rag_section = (
                "\nRELEVANT DOCUMENTATION:\n"
                f"{rag_context}"
            )

        # --------------------------------------------------------
        # Routing prompt
        # --------------------------------------------------------

        routing_prompt = f"""
You are the {self.name} Agent.

{self.system_description}

AVAILABLE TOOLS:

{self.tool_descriptions}

USER REQUEST:

{user_query}

{file_section}

{rag_section}

Your job is to select the BEST tool for the user's request.

IMPORTANT:
- Select exactly one tool.
- Provide ALL required parameters for that tool.
- Do NOT invent parameter names.
- Use the tool description above to determine the correct parameters.

For example, if code_generate requires:
- language
- task_description

then BOTH fields MUST be present.

Respond with JSON ONLY:

{{
    "tool_name": "tool_name_here",
    "tool_input": {{
        "required_parameter": "value"
    }},
    "reasoning": "brief explanation"
}}

Only include parameters relevant to the selected tool.
"""

        try:

            # ----------------------------------------------------
            # Call Groq
            # ----------------------------------------------------

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

            # ----------------------------------------------------
            # Normalize response content
            # ----------------------------------------------------

            content = response.content

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

            if not isinstance(content, str):
                content = str(content)

            # ----------------------------------------------------
            # Parse JSON
            # ----------------------------------------------------

            parsed = self._parse_json(content)

            tool_name = parsed.get(
                "tool_name",
                self.tools[0].name,
            )

            tool_input = parsed.get(
                "tool_input",
                {},
            )

            reasoning = parsed.get(
                "reasoning",
                "",
            )

            # ----------------------------------------------------
            # Make sure tool_input is a dict
            # ----------------------------------------------------

            if not isinstance(tool_input, dict):
                tool_input = {}

            # ----------------------------------------------------
            # Validate tool
            # ----------------------------------------------------

            if tool_name not in self.tool_map:

                logger.warning(
                    f"⚠️ Unknown tool selected: {tool_name}"
                )

                tool_name = self.tools[0].name

                tool_input = self._build_fallback_input(
                    user_query
                )

                reasoning = (
                    f"Invalid tool selected. "
                    f"Fallback to {tool_name}."
                )

            # ----------------------------------------------------
            # Special handling for code_generate
            # ----------------------------------------------------

            if tool_name == "code_generate":

                tool_input = self._normalize_code_generate_input(
                    tool_input,
                    user_query,
                )

            # ----------------------------------------------------
            # Inject RAG context only when tool accepts it
            # ----------------------------------------------------

            if (
                rag_context
                and self._tool_accepts_parameter(
                    tool_name,
                    "context",
                )
                and "context" not in tool_input
            ):
                tool_input["context"] = rag_context

            # ----------------------------------------------------
            # Resume file handling
            # ----------------------------------------------------

            if (
                file_content
                and self.name == "resume_agent"
                and self._tool_accepts_parameter(
                    tool_name,
                    "resume_text",
                )
                and "resume_text" not in tool_input
            ):
                tool_input["resume_text"] = file_content

            logger.info(
                f"✅ {self.name} → tool: {tool_name}"
            )

            logger.info(
                f"🔧 Tool input: {tool_input}"
            )

            return {
                **state,
                "agent_type": self.name,
                "tool_name": tool_name,
                "tool_input": tool_input,
                "rag_context": rag_context,
                "rag_sources": rag_sources,
                "iteration_count": iteration,
                "messages": [
                    AIMessage(
                        content=(
                            f"[{self.name}] "
                            f"Selected: {tool_name} | "
                            f"{reasoning}"
                        )
                    )
                ],
            }

        except Exception as e:

            logger.error(
                f"❌ {self.name} routing error: {e}"
            )

            fallback_tool = self.tools[0].name

            # ====================================================
            # Resume Agent fallback
            # ====================================================

            if (
                self.name == "resume_agent"
                and file_content
            ):
                fallback_input = {
                    "resume_text": file_content,
                }

            # ====================================================
            # PDF Agent fallback
            # ====================================================

            elif (
                self.name == "pdf_agent"
                and file_content
            ):
                fallback_input = {
                    "document_text": file_content,
                    "question": user_query,
                }

            # ====================================================
            # Other agents
            # ====================================================

            else:

                fallback_input = self._build_fallback_input(
                    user_query
                )

            logger.info(
                f"⚡ {self.name} fallback → "
                f"{fallback_tool}"
            )

            return {
                **state,
                "agent_type": self.name,
                "tool_name": fallback_tool,
                "tool_input": fallback_input,
                "rag_context": rag_context,
                "rag_sources": rag_sources,
                "iteration_count": iteration,
                "error": (
                    f"Routing fallback: {str(e)}"
                ),
                "messages": [
                    AIMessage(
                        content=(
                            f"[{self.name}] "
                            f"Fallback to {fallback_tool}"
                        )
                    )
                ],
            }

    # ============================================================
    # BUILD FALLBACK INPUT
    # ============================================================

    def _build_fallback_input(
        self,
        user_query: str,
    ) -> Dict[str, Any]:
        """
        Build valid fallback input according
        to the agent/tool.
        """

        if not self.tools:
            return {}

        tool_name = self.tools[0].name

        # --------------------------------------------------------
        # code_generate
        # --------------------------------------------------------

        if tool_name == "code_generate":

            return self._normalize_code_generate_input(
                {},
                user_query,
            )

        # --------------------------------------------------------
        # code_debug
        # --------------------------------------------------------

        if tool_name == "code_debug":

            return {
                "code": user_query,
            }

        # --------------------------------------------------------
        # code_explain
        # --------------------------------------------------------

        if tool_name == "code_explain":

            return {
                "code": user_query,
            }

        # --------------------------------------------------------
        # code_execute
        # --------------------------------------------------------

        if tool_name == "code_execute":

            return {
                "code": user_query,
            }

        # --------------------------------------------------------
        # Resume
        # --------------------------------------------------------

        if self.name == "resume_agent":

            return {
                "resume_text": user_query,
            }

        # --------------------------------------------------------
        # Generic tools
        # --------------------------------------------------------

        return {
            "query": user_query,
        }

    # ============================================================
    # NORMALIZE CODE GENERATE INPUT
    # ============================================================

    def _normalize_code_generate_input(
        self,
        tool_input: Dict[str, Any],
        user_query: str,
    ) -> Dict[str, Any]:
        """
        Ensure code_generate always receives:
            language
            task_description
        """

        if not isinstance(tool_input, dict):
            tool_input = {}

        language = (
            tool_input.get("language")
            or tool_input.get("lang")
            or self._detect_language(user_query)
        )

        task_description = (
            tool_input.get("task_description")
            or tool_input.get("description")
            or tool_input.get("task")
            or tool_input.get("query")
            or user_query
        )

        return {
            "language": language,
            "task_description": task_description,
        }

    # ============================================================
    # SIMPLE LANGUAGE DETECTION
    # ============================================================

    def _detect_language(
        self,
        query: str,
    ) -> str:
        """
        Detect programming language from user query.
        """

        text = query.lower()

        language_map = {
            "python": "Python",
            "java": "Java",
            "javascript": "JavaScript",
            "js": "JavaScript",
            "typescript": "TypeScript",
            "ts": "TypeScript",
            "c++": "C++",
            "cpp": "C++",
            "c#": "C#",
            "csharp": "C#",
            "go": "Go",
            "golang": "Go",
            "rust": "Rust",
            "php": "PHP",
            "kotlin": "Kotlin",
            "swift": "Swift",
        }

        for keyword, language in language_map.items():

            if keyword in text:
                return language

        return "Python"

    # ============================================================
    # CHECK TOOL PARAMETER
    # ============================================================

    def _tool_accepts_parameter(
        self,
        tool_name: str,
        parameter: str,
    ) -> bool:

        tool = self.tool_map.get(tool_name)

        if not tool:
            return False

        try:

            schema = tool.args_schema

            if schema is None:
                return False

            fields = getattr(
                schema,
                "model_fields",
                {},
            )

            return parameter in fields

        except Exception:

            return False

    # ============================================================
    # EXECUTE TOOL
    # ============================================================

    def execute_tool(
        self,
        state: AgentState,
    ) -> AgentState:
        """
        Execute selected tool.
        """

        tool_name = state.get(
            "tool_name",
            "",
        )

        tool_input = state.get(
            "tool_input",
            {},
        )

        logger.info(
            f"⚡ {self.name} executing: {tool_name}"
        )

        logger.info(
            f"🔧 Input: {tool_input}"
        )

        try:

            tool_fn = self.tool_map.get(
                tool_name
            )

            if not tool_fn:

                return {
                    **state,
                    "tool_output": (
                        f"Unknown tool: {tool_name}"
                    ),
                }

            result = tool_fn.invoke(
                tool_input
            )

            logger.info(
                f"✅ {self.name} tool done "
                f"({len(str(result))} chars)"
            )

            return {
                **state,
                "tool_output": result,
                "messages": [
                    AIMessage(
                        content=(
                            f"[{self.name}] "
                            f"Executed {tool_name}"
                        )
                    )
                ],
            }

        except Exception as e:

            logger.error(
                f"❌ {self.name} tool error: {e}"
            )

            return {
                **state,
                "tool_output": (
                    f"Tool error: {str(e)}"
                ),
                "messages": [
                    AIMessage(
                        content=(
                            f"[{self.name}] "
                            f"Error: {str(e)}"
                        )
                    )
                ],
            }

    # ============================================================
    # GENERATE RESPONSE
    # ============================================================

    def generate_response(
        self,
        state: AgentState,
    ) -> AgentState:
        """
        Generate final response from tool output.
        """

        tool_output = state.get(
            "tool_output",
            "",
        )

        tool_name = state.get(
            "tool_name",
            "",
        )

        # ----------------------------------------------------
# Extract structured Web results
# ----------------------------------------------------

        web_results = []

        if (
            self.name == "web_agent"
            and tool_output
            and tool_name in {
                "web_search",
                "web_search_detailed",
                "web_get_latest_news",
            }
        ):
            try:
                parsed_web_output = json.loads(
                    str(tool_output)
                )

                if isinstance(parsed_web_output, dict):
                    web_results = parsed_web_output.get(
                        "results",
                        []
                    )

            except (json.JSONDecodeError, TypeError):
                logger.warning(
                    "⚠️ Could not parse structured web results"
                )


        # ----------------------------------------------------
# Extract structured GitHub results
# ----------------------------------------------------

        github_results = []

        if (
            self.name == "github_agent"
            and tool_output
            and tool_name in {
                "github_search_repos",
                "github_get_repo_info",
                "github_get_issues",
                "github_get_pull_requests",
                "github_get_commits",
                "github_get_contributors",
                "github_get_code",
                "github_get_readme",
                "github_get_wiki",
                "github_get_releases",
                "github_get_topics",
                "github_get_languages",
                "github_get_license",
                "github_get_branches",
                "github_get_tags",
                "github_get_actions",
                "github_get_projects",
                "github_get_discussions",
                "github_get_milestones",
            }
        ):
            try:
                parsed_github_output = json.loads(
                    str(tool_output)
                )

                if isinstance(parsed_github_output, dict):
                    github_results = parsed_github_output

            except (json.JSONDecodeError, TypeError):
                logger.warning(
                    "⚠️ Could not parse structured GitHub results"
                )



        logger.info(
            f"📝 {self.name} generating final response"
        )

        system_prompt = f"""
You are the {self.name} Agent.

{self.system_description}

You executed tool:

{tool_name}

Generate a comprehensive and helpful response
based on the tool output.

Format the response clearly using markdown.

IMPORTANT FORMATTING RULES:

- Use Markdown only.
- Do NOT use HTML tags such as <br>, <div>, <p>, <table>, etc.
- Never write literal HTML tags in the response.
- Use clear Markdown headings and bullet points.
- Do not invent information that is not present in the document.

- For work experience, prefer headings and bullet points instead of wide Markdown tables.
- For skills, grouped bullet lists are preferred over very wide tables.

- Do not infer personal information unless absolutely necessary.
- Clearly label any inferred information as "Inferred".

For resume analysis, structure the response with these sections
when applicable:

## Resume Summary

## Strengths

## Weaknesses

## Skills

## Experience

## Education

## ATS Recommendations

## Improvement Suggestions

- Prefer bullet points over wide tables.
- Do not invent resume information.


Do not invent information that is not present in the resume.

For PDF Agent:
- Use sections such as:
## Document Summary
## Key Points
## Important Information
## Detailed Analysis
## Conclusion
- Prefer bullet points for important facts.
- Keep the summary concise and easy to scan.
- Do not invent facts that are not present in the document.
"""

        try:

            response = self.llm.invoke(
                [
                    SystemMessage(
                        content=system_prompt
                    ),
                    HumanMessage(
                        content=str(tool_output)
                    ),
                ]
            )

            final_response = response.content

            # ----------------------------------------------------
            # Normalize response
            # ----------------------------------------------------

            if isinstance(
                final_response,
                list,
            ):

                parts = []

                for block in final_response:

                    if isinstance(
                        block,
                        dict,
                    ):

                        text = block.get(
                            "text"
                        )

                        if text:
                            parts.append(text)

                    elif isinstance(
                        block,
                        str,
                    ):

                        parts.append(block)

                final_response = "".join(parts)

            if not isinstance(
                final_response,
                str,
            ):

                final_response = str(
                    final_response
                )

            # ----------------------------------------------------
            # RAG sources
            # ----------------------------------------------------

            rag_sources = state.get(
                "rag_sources",
                [],
            )

            if rag_sources:

                final_response += (
                    "\n\n📚 **Sources:** "
                    + ", ".join(rag_sources)
                )

            return {
                **state,
                "final_response": final_response,
                "web_results": web_results,
                "github_results": github_results,
                "messages": [
                    AIMessage(
                        content=final_response
                    )
                ],
            }

        except Exception as e:

            logger.error(
                f"❌ {self.name} response error: {e}"
            )

            return {
                **state,
                "final_response": (
                    f"Error: {str(e)}"
                ),
                "github_results": [],
                "web_results": [],
                "messages": [
                    AIMessage(
                        content=f"Error: {str(e)}"
                    )
                ],
            }

    # ============================================================
    # PARSE JSON
    # ============================================================

    def _parse_json(
        self,
        text: str,
    ) -> dict:
        """
        Safely parse JSON from an LLM response.

        Handles:
        - Markdown code fences
        - List-based content
        - Invalid control characters
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

        text = text.strip()

        # --------------------------------------------------------
        # Remove markdown fences
        # --------------------------------------------------------

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

        # --------------------------------------------------------
        # Normal JSON attempt
        # --------------------------------------------------------

        try:

            return json.loads(text)

        except json.JSONDecodeError:

            pass

        # --------------------------------------------------------
        # Extract JSON object
        # --------------------------------------------------------

        match = re.search(
            r"\{.*\}",
            text,
            re.DOTALL,
        )

        if not match:

            raise ValueError(
                "Could not find JSON object in "
                f"response: {text}"
            )

        json_text = match.group()

        # --------------------------------------------------------
        # Remove invalid control characters
        # --------------------------------------------------------

        json_text = re.sub(
            r"[\x00-\x08\x0B\x0C\x0E-\x1F]",
            " ",
            json_text,
        )

        try:

            return json.loads(
                json_text
            )

        except json.JSONDecodeError as e:

            raise ValueError(
                "Could not parse JSON from "
                f"LLM response: {e}"
            )