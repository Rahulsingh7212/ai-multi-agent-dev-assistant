from langchain_core.tools import tool
from config.settings import settings
from typing import Optional
import httpx
import logging
import json

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"


def _get_headers() -> dict:
    """Get GitHub API headers with authentication"""
    return {
        "Authorization": f"token {settings.GITHUB_PAT}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "AI-Multi-Agent-Assistant",
    }


@tool
def github_search_repos(query: str, language: Optional[str] = None, sort: str = "stars", max_results: int = 5) -> str:
    """
    Search GitHub repositories.

    Args:
        query: Search query string
        language: Filter by programming language
        sort: Sort by stars, forks, or updated
        max_results: Maximum number of results to return

    Returns:
        Search results as formatted string
    """
    logger.info(f"🔧 github_search_repos: {query}")

    try:
        params = {
            "q": f"{query} language:{language}" if language else query,
            "sort": sort,
            "per_page": max_results,
        }

        with httpx.Client(timeout=15.0) as client:
            response = client.get(
                f"{GITHUB_API_BASE}/search/repositories",
                headers=_get_headers(),
                params=params,
            )
            response.raise_for_status()
            data = response.json()

        results = []
        for repo in data.get("items", []):
            results.append(
                f"• {repo['full_name']} ⭐{repo['stargazers_count']}\n"
                f"  {repo.get('description', 'No description')}\n"
                f"  Language: {repo.get('language', 'N/A')} | "
                f"Forks: {repo['forks_count']} | "
                f"URL: {repo['html_url']}"
            )

        return "\n\n".join(results) if results else "No repositories found."

    except Exception as e:
        return f"GitHub search error: {str(e)}"


@tool
def github_get_repo_info(owner: str, repo: str) -> str:
    """
    Get detailed information about a specific GitHub repository.

    Args:
        owner: Repository owner/organization
        repo: Repository name

    Returns:
        Detailed repository information
    """
    logger.info(f"🔧 github_get_repo_info: {owner}/{repo}")

    try:
        with httpx.Client(timeout=15.0) as client:
            # Get repo info
            repo_resp = client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}",
                headers=_get_headers(),
            )
            repo_resp.raise_for_status()
            repo_data = repo_resp.json()

            # Get languages
            lang_resp = client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/languages",
                headers=_get_headers(),
            )
            languages = lang_resp.json() if lang_resp.status_code == 200 else {}

        result = f"""Repository: {repo_data['full_name']}
Description: {repo_data.get('description', 'N/A')}
Stars: {repo_data['stargazers_count']} | Forks: {repo_data['forks_count']} | Watchers: {repo_data['subscribers_count']}
Primary Language: {repo_data.get('language', 'N/A')}
All Languages: {', '.join(languages.keys()) if languages else 'N/A'}
Default Branch: {repo_data.get('default_branch', 'N/A')}
Open Issues: {repo_data['open_issues_count']}
License: {repo_data.get('license', {}).get('name', 'No license') if repo_data.get('license') else 'No license'}
Created: {repo_data['created_at'][:10]} | Updated: {repo_data['updated_at'][:10]}
URL: {repo_data['html_url']}
Clone: {repo_data['clone_url']}"""

        return result

    except Exception as e:
        return f"GitHub repo info error: {str(e)}"


@tool
def github_get_issues(owner: str, repo: str, state: str = "open", max_results: int = 5) -> str:
    """
    Get issues from a GitHub repository.

    Args:
        owner: Repository owner
        repo: Repository name
        state: Issue state (open, closed, all)
        max_results: Maximum issues to return

    Returns:
        List of issues
    """
    logger.info(f"🔧 github_get_issues: {owner}/{repo} ({state})")

    try:
        params = {"state": state, "per_page": max_results, "sort": "updated"}

        with httpx.Client(timeout=15.0) as client:
            response = client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues",
                headers=_get_headers(),
                params=params,
            )
            response.raise_for_status()
            issues = response.json()

        if not issues:
            return f"No {state} issues found in {owner}/{repo}"

        results = []
        for issue in issues:
            labels = ", ".join([l["name"] for l in issue.get("labels", [])])
            results.append(
                f"• #{issue['number']} {issue['title']}\n"
                f"  State: {issue['state']} | Author: {issue['user']['login']} | "
                f"Labels: {labels or 'None'}\n"
                f"  Created: {issue['created_at'][:10]} | "
                f"Comments: {issue['comments']}"
            )

        return "\n\n".join(results)

    except Exception as e:
        return f"GitHub issues error: {str(e)}"


@tool
def github_get_pull_requests(owner: str, repo: str, state: str = "open", max_results: int = 5) -> str:
    """
    Get pull requests from a GitHub repository.

    Args:
        owner: Repository owner
        repo: Repository name
        state: PR state (open, closed, all)
        max_results: Maximum PRs to return

    Returns:
        List of pull requests
    """
    logger.info(f"🔧 github_get_pull_requests: {owner}/{repo} ({state})")

    try:
        params = {"state": state, "per_page": max_results, "sort": "updated"}

        with httpx.Client(timeout=15.0) as client:
            response = client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls",
                headers=_get_headers(),
                params=params,
            )
            response.raise_for_status()
            prs = response.json()

        if not prs:
            return f"No {state} pull requests found in {owner}/{repo}"

        results = []
        for pr in prs:
            results.append(
                f"• #{pr['number']} {pr['title']}\n"
                f"  State: {pr['state']} | Author: {pr['user']['login']}\n"
                f"  Branch: {pr['head']['ref']} → {pr['base']['ref']}\n"
                f"  Created: {pr['created_at'][:10]} | "
                f"Review Comments: {pr['review_comments']}"
            )

        return "\n\n".join(results)

    except Exception as e:
        return f"GitHub PRs error: {str(e)}"


# ============================
# TOOL REGISTRY
# ============================
GITHUB_AGENT_TOOLS = [github_search_repos, github_get_repo_info, github_get_issues, github_get_pull_requests]

GITHUB_TOOL_MAP = {
    "github_search_repos": github_search_repos,
    "github_get_repo_info": github_get_repo_info,
    "github_get_issues": github_get_issues,
    "github_get_pull_requests": github_get_pull_requests,
}