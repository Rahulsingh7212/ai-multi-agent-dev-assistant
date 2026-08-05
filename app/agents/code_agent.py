from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import render_text_description
from app.agents.state import AgentState, create_initial_state
from app.agents.rag_helper import get_rag_context
from app.tools.code_tools import CODE_AGENT_TOOLS, TOOL_MAP
from config.settings import settings
from typing import Dict, Any
import json
import logging
import re

logger = logging.getLogger(__name__)


class CodeAgent:
    """
    Code Agent built with LangGraph.

    Capabilities:
    - code_generate: Generate code in any language
    - code_debug: Debug and fix buggy code
    - code_explain: Explain what code does
    - code_execute: Safely run Python snippets

    Enhanced with RAG context from ingested documentation.
    """

    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=settings.LLM_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.3,  # Lower temperature for code tasks
            max_output_tokens=settings.LLM_MAX_TOKENS,
        )

        self.tools = CODE_AGENT_TOOLS
        self.tool_map = TOOL_MAP

        # Tool descriptions for the system prompt
        self.tool_descriptions = render_text_description(self.tools)

        logger.info("✅ CodeAgent initialized with 4 tools")

    # ============================
    # NODE 1: ROUTER
    # ============================

    def route_query(self, state: AgentState) -> AgentState:
        """
        Analyze the user query and decide which tool to use.
        This is the BRAIN of the agent.
        """
        user_query = state["user_query"]
        iteration = state.get("iteration_count", 0) + 1

        logger.info(f"🔀 CodeAgent routing (iteration {iteration}): {user_query[:80]}...")

        # Get RAG context if available
        rag_result = get_rag_context(user_query, k=3)
        rag_context = rag_result["context"]
        rag_sources = rag_result["sources"]

        # Build routing prompt
        rag_section = ""
        if rag_context:
            rag_section = f"""
RELEVANT DOCUMENTATION CONTEXT:
{rag_context}

Use this documentation context when generating or explaining code.
"""

        routing_prompt = f"""You are a Code Agent — an expert AI assistant for software development.

AVAILABLE TOOLS:
{self.tool_descriptions}

USER REQUEST: {user_query}
{rag_section}

Based on the user request, decide which tool to call and what parameters to pass.

Respond with a JSON object ONLY (no markdown, no code fences):
{{
    "tool_name": "name_of_tool",
    "tool_input": {{
        "language": "python",
        "task_description": "...",
        "code": "...",
        "error_message": "...",
        "detail_level": "medium"
    }},
    "reasoning": "Why you chose this tool"
}}

Only include the parameters that are relevant for the chosen tool.
If the user asks to generate code, use code_generate.
If the user reports a bug or error, use code_debug.
If the user asks to understand code, use code_explain.
If the user asks to run/test code, use code_execute."""

        try:
            response = self.llm.invoke([SystemMessage(content=routing_prompt)])
            parsed = self._parse_json_response(response.content)

            tool_name = parsed.get("tool_name", "code_generate")
            tool_input = parsed.get("tool_input", {})
            reasoning = parsed.get("reasoning", "")

            # Inject RAG context into tool input if available
            if rag_context and "context" not in tool_input:
                tool_input["context"] = rag_context

            logger.info(f"✅ Routed to tool: {tool_name} | Reasoning: {reasoning}")

            return {
                **state,
                "agent_type": "code_agent",
                "tool_name": tool_name,
                "tool_input": tool_input,
                "rag_context": rag_context,
                "rag_sources": rag_sources,
                "iteration_count": iteration,
                "messages": [
                    AIMessage(
                        content=f"[Router] Selected tool: {tool_name} | Reasoning: {reasoning}"
                    )
                ],
            }

        except Exception as e:
            logger.error(f"❌ Routing failed: {e}")
            return {
                **state,
                "agent_type": "code_agent",
                "tool_name": "code_generate",
                "tool_input": {"language": "python", "task_description": user_query},
                "rag_context": rag_context,
                "rag_sources": rag_sources,
                "iteration_count": iteration,
                "error": f"Routing fallback: {str(e)}",
                "messages": [
                    AIMessage(content=f"[Router] Fallback to code_generate due to error")
                ],
            }

    # ============================
    # NODE 2: TOOL EXECUTOR
    # ============================

    def execute_tool(self, state: AgentState) -> AgentState:
        """
        Execute the selected tool with the provided input.
        The tool returns a prompt that the LLM will use to generate the final answer.
        """
        tool_name = state.get("tool_name", "code_generate")
        tool_input = state.get("tool_input", {})

        logger.info(f"⚡ Executing tool: {tool_name}")

        try:
            # Get the tool function
            tool_fn = self.tool_map.get(tool_name)

            if not tool_fn:
                return {
                    **state,
                    "tool_output": f"Error: Unknown tool '{tool_name}'",
                    "messages": [
                        AIMessage(content=f"[Tool] Error: Unknown tool '{tool_name}'")
                    ],
                }

            # Execute the tool
            tool_result = tool_fn.invoke(tool_input)

            logger.info(f"✅ Tool executed: {tool_name} ({len(str(tool_result))} chars)")

            return {
                **state,
                "tool_output": tool_result,
                "messages": [
                    AIMessage(content=f"[Tool] Executed {tool_name} successfully")
                ],
            }

        except Exception as e:
            logger.error(f"❌ Tool execution failed: {e}")
            return {
                **state,
                "tool_output": f"Tool execution error: {str(e)}",
                "messages": [
                    AIMessage(content=f"[Tool] Error: {str(e)}")
                ],
            }

    # ============================
    # NODE 3: RESPONSE GENERATOR
    # ============================

    def generate_response(self, state: AgentState) -> AgentState:
        """
        Take the tool output and generate the final human-readable response.
        The tool output is actually a prompt for the LLM.
        """
        tool_output = state.get("tool_output", "")
        tool_name = state.get("tool_name", "")
        user_query = state["user_query"]
        rag_context = state.get("rag_context")

        logger.info(f"📝 Generating final response from {tool_name} output")

        # The tool_output IS the prompt for the LLM
        # We just pass it through to generate the actual response
        system_prompt = f"""You are an expert Code Agent AI Assistant.
You have already selected and executed a tool: {tool_name}
The tool has prepared a detailed prompt for you.

Now generate the actual code/explanation based on that prompt.
Be thorough, accurate, and provide production-quality output.

If the user provided code, preserve their variable names and structure.
If generating code, make it complete, runnable, and well-documented."""

        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=tool_output),
])

# Convert Gemini response to plain text
            if isinstance(response.content, str):
                final_response = response.content

            elif isinstance(response.content, list):
                parts = []

                for item in response.content:
                    if isinstance(item, dict):
                        parts.append(item.get("text", ""))
                    elif hasattr(item, "text"):
                        parts.append(item.text)
                    else:
                        parts.append(str(item))

                final_response = "".join(parts)

            else:
                final_response = str(response.content)
            rag_sources = state.get("rag_sources", [])

            if rag_sources:
                citation = "\n\n📚 **Sources:** " + ", ".join(rag_sources)
                final_response += citation

            logger.info(f"✅ Final response generated ({len(final_response)} chars)")

            return {
                **state,
                "final_response": final_response,
                "messages": [AIMessage(content=final_response)],
            }

        except Exception as e:
            logger.error(f"❌ Response generation failed: {e}")
            return {
                **state,
                "final_response": f"Error generating response: {str(e)}",
                "messages": [AIMessage(content=f"Error: {str(e)}")],
            }

    # ============================
    # HELPERS
    # ============================

    def _parse_json_response(self, text: str) -> dict:
        """Parse JSON from LLM response, handling markdown fences"""
        # Remove markdown code fences if present
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON object in the text
            match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
            if match:
                return json.loads(match.group())
            raise


# ============================
# Singleton instance
# ============================
code_agent = CodeAgent()
