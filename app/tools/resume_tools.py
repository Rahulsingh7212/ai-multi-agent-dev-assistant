from langchain_core.tools import tool
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@tool
def resume_parse(resume_text: str) -> str:
    """
    Parse and extract structured information from resume text.

    Args:
        resume_text: Raw text content of the resume

    Returns:
        Structured resume information prompt for LLM
    """
    logger.info(f"🔧 resume_parse called ({len(resume_text)} chars)")

    prompt = f"""Parse the following resume and extract structured information:

RESUME TEXT:
{resume_text}

Extract and organize the following sections:
1. **Contact Information**: Name, email, phone, location, LinkedIn/GitHub
2. **Professional Summary**: Brief professional overview
3. **Skills**: Technical skills, tools, frameworks, languages
4. **Work Experience**: Each position with company, title, dates, key achievements
5. **Education**: Degrees, institutions, graduation dates, GPA if mentioned
6. **Certifications**: Any professional certifications
7. **Projects**: Notable projects with descriptions
8. **Missing Sections**: What important sections are missing?

Format the output as a clean, structured summary."""

    return prompt


@tool
def resume_analyze(resume_text: str, target_role: Optional[str] = None) -> str:
    """
    Analyze a resume for quality, strengths, and weaknesses.

    Args:
        resume_text: Raw text content of the resume
        target_role: Optional target job role to evaluate against

    Returns:
        Resume analysis prompt for LLM
    """
    logger.info(f"🔧 resume_analyze called (target: {target_role})")

    target_section = ""
    if target_role:
        target_section = f"""
TARGET ROLE: {target_role}
Evaluate how well this resume aligns with the target role.
Identify gaps between the resume and typical requirements for {target_role}."""

    prompt = f"""Perform a comprehensive analysis of the following resume:

RESUME TEXT:
{resume_text}
{target_section}

Provide analysis on:
1. **Overall Score**: Rate 1-10 with justification
2. **Strengths**: What stands out positively (be specific)
3. **Weaknesses**: What needs improvement (be specific)
4. **ATS Compatibility**: How likely to pass Applicant Tracking Systems
5. **Impact Score**: Are achievements quantified? Action verbs used?
6. **Formatting Issues**: Any structural or formatting problems
7. **Keyword Analysis**: Important keywords present/missing
8. **Recommendations**: Top 5 specific improvements to make"""

    return prompt


@tool
def resume_improve(resume_text: str, target_role: Optional[str] = None) -> str:
    """
    Generate an improved version of the resume with specific suggestions.

    Args:
        resume_text: Raw text content of the resume
        target_role: Optional target job role to optimize for

    Returns:
        Resume improvement prompt for LLM
    """
    logger.info(f"🔧 resume_improve called (target: {target_role})")

    target_section = ""
    if target_role:
        target_section = f"\nOptimize the resume for the role: {target_role}"

    prompt = f"""Improve the following resume with specific, actionable changes:

ORIGINAL RESUME:
{resume_text}
{target_section}

Provide:
1. **Improved Bullet Points**: Rewrite weak bullet points with strong action verbs and quantified results
2. **Missing Sections to Add**: What sections should be added
3. **Skills to Highlight**: Skills that should be more prominent
4. **Suggested Summary**: An improved professional summary
5. **Keywords to Add**: Industry keywords that should be included
6. **Before/After Examples**: Show 3-5 specific bullet point improvements (before → after)

Rules for improvements:
- Use strong action verbs (Led, Developed, Implemented, Optimized, etc.)
- Quantify achievements with numbers, percentages, metrics
- Remove vague language ("helped with", "worked on")
- Be specific about technologies and impact"""

    return prompt


# ============================
# TOOL REGISTRY
# ============================
RESUME_AGENT_TOOLS = [resume_parse, resume_analyze, resume_improve]

RESUME_TOOL_MAP = {
    "resume_parse": resume_parse,
    "resume_analyze": resume_analyze,
    "resume_improve": resume_improve,
}