from langchain_google_genai import ChatGoogleGenerativeAI
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
    Each agent has: router → tool_executor → response_generator
    This class eliminates code duplication across agents.
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

        self.llm = ChatGoogleGenerativeAI(
            model=settings.LLM_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=temperature,
            max_output_tokens=settings.LLM_MAX_TOKENS,
        )

        logger.info(f"✅ {name} agent initialized with {len(tools)} tools")

    def route_query(self, state: AgentState) -> AgentState:
        """Analyze query and select tool."""
        user_query = state["user_query"]
        iteration = state.get("iteration_count", 0) + 1

        logger.info(f"🔀 {self.name} routing (iter {iteration}): {user_query[:60]}...")

        # Get RAG context
        rag_result = get_rag_context(user_query, k=3)
        rag_context = rag_result["context"]
        rag_sources = rag_result["sources"]

        # Check for uploaded file content
        file_content = state.get("uploaded_file_content", "")
        file_section = ""
        if file_content:
            file_section = f"\nUPLOADED FILE CONTENT:\n{file_content[:3000]}\n\nUse this content for your analysis."

        rag_section = ""
        if rag_context:
            rag_section = f"\nRELEVANT DOCUMENTATION:\n{rag_context}"

        routing_prompt = f"""You are the {self.name} Agent.
{self.system_description}

AVAILABLE TOOLS:
{self.tool_descriptions}

USER REQUEST: {user_query}
{file_section}
{rag_section}

Select the best tool and parameters. Respond with JSON ONLY:
{{
    "tool_name": "tool_name_here",
    "tool_input": {{}},
    "reasoning": "why this tool"
}}

Only include relevant parameters for the chosen tool."""

        try:
            response = self.llm.invoke([SystemMessage(content=routing_prompt)])
            parsed = self._parse_json(response.content)

            tool_name = parsed.get("tool_name", self.tools[0].name)
            tool_input = parsed.get("tool_input", {})
            reasoning = parsed.get("reasoning", "")

            # Inject RAG context if tool supports it
            if rag_context and "context" not in tool_input:
                tool_input["context"] = rag_context

            # Inject file content if tool supports it
            if file_content and "resume_text" not in tool_input and self.name == "resume_agent":
                tool_input["resume_text"] = file_content

            logger.info(f"✅ {self.name} → tool: {tool_name}")

            return {
                **state,
                "agent_type": self.name,
                "tool_name": tool_name,
                "tool_input": tool_input,
                "rag_context": rag_context,
                "rag_sources": rag_sources,
                "iteration_count": iteration,
                "messages": [AIMessage(content=f"[{self.name}] Selected: {tool_name} | {reasoning}")],
            }

        except Exception as e:
            logger.error(f"❌ {self.name} routing error: {e}")
            fallback_tool = self.tools[0].name
            fallback_input = {"query": user_query, "question": user_query}
            if file_content and self.name == "resume_agent":
                fallback_input = {"resume_text": file_content}

            return {
                **state,
                "agent_type": self.name,
                "tool_name": fallback_tool,
                "tool_input": fallback_input,
                "rag_context": rag_context,
                "rag_sources": rag_sources,
                "iteration_count": iteration,
                "error": f"Routing fallback: {str(e)}",
                "messages": [AIMessage(content=f"[{self.name}] Fallback to {fallback_tool}")],
            }

    def execute_tool(self, state: AgentState) -> AgentState:
        """Execute the selected tool."""
        tool_name = state.get("tool_name", "")
        tool_input = state.get("tool_input", {})

        logger.info(f"⚡ {self.name} executing: {tool_name}")

        try:
            tool_fn = self.tool_map.get(tool_name)
            if not tool_fn:
                return {**state, "tool_output": f"Unknown tool: {tool_name}"}

            result = tool_fn.invoke(tool_input)
            logger.info(f"✅ {self.name} tool done ({len(str(result))} chars)")

            return {
                **state,
                "tool_output": result,
                "messages": [AIMessage(content=f"[{self.name}] Executed {tool_name}")],
            }

        except Exception as e:
            logger.error(f"❌ {self.name} tool error: {e}")
            return {
                **state,
                "tool_output": f"Tool error: {str(e)}",
                "messages": [AIMessage(content=f"[{self.name}] Error: {str(e)}")],
            }

    def generate_response(self, state: AgentState) -> AgentState:
        """Generate final response from tool output."""
        tool_output = state.get("tool_output", "")
        tool_name = state.get("tool_name", "")

        logger.info(f"📝 {self.name} generating final response")

        system_prompt = f"""You are the {self.name} Agent.
{self.system_description}
You executed tool: {tool_name}.
Generate a comprehensive, helpful response based on the tool output.
Format the response clearly with markdown."""

        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=str(tool_output)),
            ])

            final_response = response.content
            rag_sources = state.get("rag_sources", [])

            if rag_sources:
                final_response += "\n\n📚 **Sources:** " + ", ".join(rag_sources)

            return {
                **state,
                "final_response": final_response,
                "messages": [AIMessage(content=final_response)],
            }

        except Exception as e:
            logger.error(f"❌ {self.name} response error: {e}")
            return {
                **state,
                "final_response": f"Error: {str(e)}",
                "messages": [AIMessage(content=f"Error: {str(e)}")],
            }

    def _parse_json(self, text: str) -> dict:
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
            if match:
                return json.loads(match.group())
            raise