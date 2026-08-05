from app.agents.code_graph import code_agent_graph
from app.agents.state import create_initial_state, AgentState
from app.agents.memory import conversation_memory
from typing import Dict, Any, Optional
import logging
import uuid

logger = logging.getLogger(__name__)


class AgentService:
    """
    Service layer for running agents.
    Manages graph execution and conversation memory.
    """

    def run_code_agent(
        self,
        query: str,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Run the Code Agent graph for a user query.

        Steps:
        1. Create initial state (with conversation history)
        2. Execute the LangGraph
        3. Store result in conversation memory
        4. Return the final response
        """
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())

        logger.info(f"🤖 Code Agent invoked | Session: {session_id} | Query: {query[:80]}...")

        # Store user message in memory
        conversation_memory.add_message(session_id, "human", query)

        # Create initial state
        initial_state = create_initial_state(
            user_query=query,
            session_id=session_id,
        )

        # Add conversation history to state messages
        history = conversation_memory.get_history(session_id)
        if history:
            initial_state["messages"] = list(history)

        try:
            # Execute the graph
            final_state = code_agent_graph.invoke(initial_state)

            # Extract final response
            response = final_state.get("final_response", "No response generated")

            # Store AI response in memory
            conversation_memory.add_message(session_id, "ai", response)

            # Build result
            result = {
                "response": response,
                "tool_used": final_state.get("tool_name", "unknown"),
                "agent_type": final_state.get("agent_type", "code_agent"),
                "session_id": session_id,
                "rag_sources": final_state.get("rag_sources", []),
                "has_rag_context": final_state.get("rag_context") is not None,
                "iterations": final_state.get("iteration_count", 0),
            }

            logger.info(
                f"✅ Code Agent completed | Tool: {result['tool_used']} | "
                f"RAG: {result['has_rag_context']} | "
                f"Response: {len(response)} chars"
            )

            return result

        except Exception as e:
            logger.error(f"❌ Code Agent execution failed: {e}")

            # Store error in memory
            error_msg = f"Agent error: {str(e)}"
            conversation_memory.add_message(session_id, "ai", error_msg)

            return {
                "response": f"I encountered an error processing your request: {str(e)}",
                "tool_used": "error",
                "agent_type": "code_agent",
                "session_id": session_id,
                "rag_sources": [],
                "has_rag_context": False,
                "iterations": 0,
                "error": str(e),
            }


# ============================
# Singleton instance
# ============================
agent_service = AgentService()