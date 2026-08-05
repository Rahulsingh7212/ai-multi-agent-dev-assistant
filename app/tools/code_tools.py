from langchain_core.tools import tool
from langchain_experimental.utilities import PythonREPL
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Safe Python REPL instance
python_repl = PythonREPL()


# ============================
# TOOL 1: CODE GENERATOR
# ============================

@tool
def code_generate(
    language: str,
    task_description: str,
    context: Optional[str] = None,
) -> str:
    """
    Generate code in the specified language for the given task.

    Args:
        language: Programming language (python, javascript, etc.)
        task_description: What the code should do
        context: Optional RAG context from documentation

    Returns:
        Generated code as a string
    """
    logger.info(f"🔧 code_generate called: {language} — {task_description[:50]}...")

    context_section = ""
    if context:
        context_section = f"""
REFERENCE DOCUMENTATION:
{context}
Use the above documentation to ensure the code follows best practices.
"""

    prompt = f"""Generate clean, production-ready {language} code for the following task:

TASK: {task_description}
{context_section}

Requirements:
- Include proper error handling
- Add type hints/annotations where applicable
- Include docstrings
- Follow {language} best practices
- Make the code self-contained and runnable

Return ONLY the code, no explanations outside the code comments."""

    return prompt


# ============================
# TOOL 2: CODE DEBUGGER
# ============================

@tool
def code_debug(
    code: str,
    error_message: str,
    language: str = "python",
    context: Optional[str] = None,
) -> str:
    """
    Debug and fix code that has errors.

    Args:
        code: The buggy code
        error_message: The error message or unexpected behavior
        language: Programming language of the code
        context: Optional RAG context from documentation

    Returns:
        Debugging instructions and fixed code
    """
    logger.info(f"🔧 code_debug called: {language} — {error_message[:50]}...")

    context_section = ""
    if context:
        context_section = f"""
REFERENCE DOCUMENTATION:
{context}
"""

    prompt = f"""Debug the following {language} code:

CODE:
{code}

ERROR/ISSUE:
{error_message}
{context_section}
Provide:
1. Root cause analysis
2. The corrected code (complete, ready to run)
3. Explanation of what was wrong and how it was fixed"""

    return prompt


# ============================
# TOOL 3: CODE EXPLAINER
# ============================

@tool
def code_explain(
    code: str,
    language: str = "python",
    detail_level: str = "medium",
    context: Optional[str] = None,
) -> str:
    """
    Explain code in detail, breaking down what each part does.

    Args:
        code: The code to explain
        language: Programming language
        detail_level: brief, medium, or detailed
        context: Optional RAG context from documentation

    Returns:
        Detailed explanation of the code
    """
    logger.info(f"🔧 code_explain called: {language} — detail: {detail_level}")

    context_section = ""
    if context:
        context_section = f"""
This code uses the following library/framework. Here is its documentation:
{context}
"""

    detail_instructions = {
        "brief": "Give a short summary of what the code does (2-3 sentences).",
        "medium": "Explain each major section/block of the code. Include line-by-line for complex parts.",
        "detailed": "Explain every line of code. Include: purpose, how it works, alternatives, and best practices.",
    }

    instruction = detail_instructions.get(detail_level, detail_instructions["medium"])

    prompt = f"""Explain the following {language} code:
{code}

{context_section}

{instruction}
Format the explanation with:
- Overview: What the code does overall
- Breakdown: Section-by-section explanation
- Key Concepts: Important patterns or concepts used"""

    return prompt


# ============================
# TOOL 4: SAFE CODE EXECUTION
# ============================

@tool
def code_execute(code: str) -> str:
    """
    Safely execute Python code and return the output.
    Use only for testing simple Python snippets.
    WARNING: This uses a sandboxed REPL but is not fully secure.

    Args:
        code: Python code to execute

    Returns:
        Output of the code execution
    """
    logger.info("🔧 code_execute called")

    # Safety check - block dangerous operations
    dangerous_patterns = [
        "import os",
        "import subprocess",
        "import sys",
        "os.system",
        "subprocess",
        "__import__",
        "eval(",
        "exec(",
        "open(",
        "shutil.",
        "pathlib",
    ]

    for pattern in dangerous_patterns:
        if pattern in code:
            return f"⚠️ BLOCKED: Code contains potentially unsafe pattern '{pattern}'. Execution denied for security."

    try:
        result = python_repl.run(code)
        return f"✅ Output:\n{result}" if result else "✅ Code executed successfully (no output)"

    except Exception as e:
        return f"❌ Execution Error:\n{type(e).__name__}: {str(e)}"


# ============================
# TOOL REGISTRY
# ============================

CODE_AGENT_TOOLS = [
    code_generate,
    code_debug,
    code_explain,
    code_execute,
]

TOOL_MAP = {
    "code_generate": code_generate,
    "code_debug": code_debug,
    "code_explain": code_explain,
    "code_execute": code_execute,
}