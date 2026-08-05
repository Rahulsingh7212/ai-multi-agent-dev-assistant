from typing import TypedDict, List, Dict, Any, Optional, Annotated
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import operator


class AgentState(TypedDict):
    """
    Shared state that flows through all nodes in the LangGraph.

    This is the 'memory' of the agent graph.
    Every node reads from and writes to this state.
    """

    # ============================
    # Conversation History
    # ============================
    # 'operator.add' means new messages are APPENDED
    # instead of overwriting the list
    messages: Annotated[List[BaseMessage], operator.add]

    # ============================
    # Current Interaction
    # ============================
    user_query: str                        # Original user question
    agent_type: str                        # Which agent is handling this
    tool_name: Optional[str]               # Which tool was selected
    tool_input: Optional[Dict[str, Any]]   # Input passed to the tool
    tool_output: Optional[str]             # Result from the tool

    # ============================
    # RAG Context
    # ============================
    rag_context: Optional[str]             # Retrieved document context
    rag_sources: Optional[List[str]]       # Source citations

    # ============================
    # Final Output
    # ============================
    final_response: Optional[str]          # The answer to return to user

    # ============================
    # Metadata
    # ============================
    session_id: Optional[str]              # Session tracking
    iteration_count: int                   # Prevent infinite loops
    error: Optional[str]                   # Error message if any


def create_initial_state(
    user_query: str,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Factory function to create a fresh AgentState
    for a new conversation turn.
    """
    return {
        "messages": [HumanMessage(content=user_query)],
        "user_query": user_query,
        "agent_type": "",
        "tool_name": None,
        "tool_input": None,
        "tool_output": None,
        "rag_context": None,
        "rag_sources": None,
        "final_response": None,
        "session_id": session_id or "default",
        "iteration_count": 0,
        "error": None,
    }