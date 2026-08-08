from app.agents.generic_agent import GenericAgent
from app.tools.code_tools import CODE_AGENT_TOOLS, TOOL_MAP
from app.tools.resume_tools import RESUME_AGENT_TOOLS, RESUME_TOOL_MAP
from app.tools.pdf_tools import PDF_AGENT_TOOLS, PDF_TOOL_MAP
from app.tools.github_tools import GITHUB_AGENT_TOOLS, GITHUB_TOOL_MAP
from app.tools.web_tools import WEB_AGENT_TOOLS, WEB_TOOL_MAP
import logging

logger = logging.getLogger(__name__)


# ============================
# CODE AGENT
# ============================
code_agent = GenericAgent(
    name="code_agent",
    tools=CODE_AGENT_TOOLS,
    tool_map=TOOL_MAP,
    system_description=(
        "You are a Code Agent — expert in writing, debugging, "
        "explaining, and executing code in any programming language."
    ),
    temperature=0.3,
)

# ============================
# RESUME AGENT
# ============================
resume_agent = GenericAgent(
    name="resume_agent",
    tools=RESUME_AGENT_TOOLS,
    tool_map=RESUME_TOOL_MAP,
    system_description=(
        "You are a Resume Agent — expert at parsing, analyzing, "
        "and improving resumes. You help users optimize their resumes "
        "for ATS systems and specific job roles."
    ),
    temperature=0.4,
)

# ============================
# PDF AGENT
# ============================
pdf_agent = GenericAgent(
    name="pdf_agent",
    tools=PDF_AGENT_TOOLS,
    tool_map=PDF_TOOL_MAP,
    system_description=(
        "You are a PDF Document Agent — expert at answering questions "
        "about documents, summarizing content, and comparing documents "
        "using RAG retrieval."
    ),
    temperature=0.3,
)

# ============================
# GITHUB AGENT
# ============================
github_agent = GenericAgent(
    name="github_agent",
    tools=GITHUB_AGENT_TOOLS,
    tool_map=GITHUB_TOOL_MAP,
    system_description=(
        "You are a GitHub Agent — expert at searching repositories, "
        "fetching repo information, issues, and pull requests using "
        "the GitHub API."
    ),
    temperature=0.3,
)

# ============================
# WEB AGENT
# ============================
web_agent = GenericAgent(
    name="web_agent",
    tools=WEB_AGENT_TOOLS,
    tool_map=WEB_TOOL_MAP,
    system_description=(
        "You are a Web Search Agent — expert at finding real-time "
        "information, latest news, and detailed web research using "
        "Tavily search."
    ),
    temperature=0.4,
)


# ============================
# AGENT REGISTRY
# ============================
AGENT_REGISTRY = {
    "code_agent": code_agent,
    "resume_agent": resume_agent,
    "pdf_agent": pdf_agent,
    "github_agent": github_agent,
    "web_agent": web_agent,
}

logger.info(f"✅ All agents initialized: {list(AGENT_REGISTRY.keys())}")