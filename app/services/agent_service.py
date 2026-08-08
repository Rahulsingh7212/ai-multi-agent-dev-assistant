from app.agents.supervisor_graph import supervisor_graph
from langchain_core.messages import AIMessage
from app.agents.state import create_initial_state, AgentState
from app.agents.persistent_memory import persistent_memory
from app.tools.registry import tool_registry
from config.settings import settings
from typing import Dict, Any, Optional
from app.utils.retry import general_retry
import logging
import uuid

logger = logging.getLogger(__name__)


class AgentService:
    """
    Service layer for running the multi-agent system.
    Now with Redis-backed persistent memory.
    """

    @general_retry
    def run_agent(
        self,
        query: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        uploaded_file_path: Optional[str] = None,
        uploaded_file_content: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Run the Multi-Agent Supervisor Graph with persistent memory.
        """
        if not session_id:
            session_id = str(uuid.uuid4())

        logger.info(
            f"🤖 Multi-Agent invoked | User: {user_id or 'anonymous'} | "
            f"Session: {session_id} | Query: {query[:80]}..."
        )

        # Store user message in persistent memory
        persistent_memory.add_message(
            session_id=session_id,
            role="human",
            content=query,
            user_id=user_id,
        )

        # Create initial state
        initial_state = create_initial_state(
            user_query=query,
            session_id=session_id,
            uploaded_file_path=uploaded_file_path,
            uploaded_file_content=uploaded_file_content,
        )

        # Load conversation history from persistent memory
        history = persistent_memory.get_history(
            session_id=session_id,
            user_id=user_id,
        )
        if history:
            initial_state["messages"] = list(history)

        try:
            # Execute the supervisor graph
            final_state = supervisor_graph.invoke(initial_state)

            response = final_state.get("final_response", "No response generated")
            next_agent = final_state.get("next_agent", "unknown")
            tool_used = final_state.get("tool_name", "unknown")
            supervisor_reasoning = final_state.get("supervisor_reasoning", "")

            # Store AI response in persistent memory
            persistent_memory.add_message(
                session_id=session_id,
                role="ai",
                content=response,
                user_id=user_id,
            )

            result = {
                "response": response,
                "agent_used": next_agent,
                "tool_used": tool_used,
                "supervisor_reasoning": supervisor_reasoning,
                "session_id": session_id,
                "user_id": user_id,
                "rag_sources": final_state.get("rag_sources", []),
                "has_rag_context": final_state.get("rag_context") is not None,
                "iterations": final_state.get("iteration_count", 0),
                "memory_backend": settings.MEMORY_BACKEND,
            }

            logger.info(
                f"✅ Agent completed | Supervisor→{next_agent} | "
                f"Tool: {tool_used} | Memory: {settings.MEMORY_BACKEND}"
            )

            return result

        except Exception as e:
            logger.error(f"❌ Multi-Agent execution failed: {e}")

            error_msg = f"Agent error: {str(e)}"
            persistent_memory.add_message(
                session_id=session_id,
                role="ai",
                content=error_msg,
                user_id=user_id,
            )

            return {
                "response": f"I encountered an error: {str(e)}",
                "agent_used": "error",
                "tool_used": "error",
                "supervisor_reasoning": "",
                "session_id": session_id,
                "user_id": user_id,
                "rag_sources": [],
                "has_rag_context": False,
                "iterations": 0,
                "memory_backend": settings.MEMORY_BACKEND,
                "error": str(e),
            }


# ============================
# Singleton
# ============================
agent_service = AgentService()