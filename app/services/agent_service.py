from app.agents.supervisor_graph import supervisor_graph
from app.agents.state import create_initial_state, AgentState
from app.agents.memory import conversation_memory
from typing import Dict, Any, Optional
import logging
import uuid

logger = logging.getLogger(__name__)


class AgentService:
    """
    Service layer for running the multi-agent system.
    """

    def run_agent(
        self,
        query: str,
        session_id: Optional[str] = None,
        uploaded_file_path: Optional[str] = None,
        uploaded_file_content: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Run the Multi-Agent Supervisor Graph.

        Steps:
        1. Supervisor analyzes query → picks agent
        2. Selected agent routes → executes tool → generates response
        3. Store in conversation memory
        4. Return result
        """
        if not session_id:
            session_id = str(uuid.uuid4())

        logger.info(f"🤖 Multi-Agent invoked | Session: {session_id} | Query: {query[:80]}...")

        # Store user message
        conversation_memory.add_message(session_id, "human", query)

        # Create initial state
        initial_state = create_initial_state(
            user_query=query,
            session_id=session_id,
            uploaded_file_path=uploaded_file_path,
            uploaded_file_content=uploaded_file_content,
        )

        # Add conversation history
        history = conversation_memory.get_history(session_id)
        if history:
            initial_state["messages"] = list(history)

        try:
            # Execute the supervisor graph
            final_state = supervisor_graph.invoke(initial_state)

            response = final_state.get("final_response", "No response generated")
            next_agent = final_state.get("next_agent", "unknown")
            tool_used = final_state.get("tool_name", "unknown")
            supervisor_reasoning = final_state.get("supervisor_reasoning", "")

            # Store AI response in memory
            conversation_memory.add_message(session_id, "ai", response)

            result = {
                "response": response,
                "agent_used": next_agent,
                "tool_used": tool_used,
                "supervisor_reasoning": supervisor_reasoning,
                "session_id": session_id,
                "rag_sources": final_state.get("rag_sources", []),
                "has_rag_context": final_state.get("rag_context") is not None,
                "iterations": final_state.get("iteration_count", 0),
            }

            logger.info(
                f"✅ Agent completed | Supervisor→{next_agent} | "
                f"Tool: {tool_used} | Response: {len(response)} chars"
            )

            return result

        except Exception as e:
            logger.error(f"❌ Multi-Agent execution failed: {e}")
            error_msg = f"Agent error: {str(e)}"
            conversation_memory.add_message(session_id, "ai", error_msg)

            return {
                "response": f"I encountered an error: {str(e)}",
                "agent_used": "error",
                "tool_used": "error",
                "supervisor_reasoning": "",
                "session_id": session_id,
                "rag_sources": [],
                "has_rag_context": False,
                "iterations": 0,
                "error": str(e),
            }


# ============================
# Singleton
# ============================
agent_service = AgentService()