from langchain_core.tools import tool
from config.settings import settings
from typing import Optional
import httpx
import logging
import json

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"


def _get_headers() -> dict:
    """Get GitHub API headers with authentication."""
    return {
        "Authorization": f"token {settings.GITHUB_PAT}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "AI-Multi-Agent-Assistant",
    }


# ============================================================
# SEARCH REPOSITORIES
# ============================================================

@tool
def github_search_repos(
    query: str,
    language: Optional[str] = None,
    sort: str = "stars",
    max_results: int = 5,
) -> str:
    """
    Search GitHub repositories.

    Returns structured JSON for frontend rendering.
    """

    logger.info(
        f"🔧 github_search_repos: {query}"
    )

    try:
        params = {
            "q": (
                f"{query} language:{language}"
                if language
                else query
            ),
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

        repositories = []

        for repo in data.get("items", []):

            repositories.append({
                "full_name": repo.get(
                    "full_name",
                    "",
                ),
                "name": repo.get(
                    "name",
                    "",
                ),
                "owner": repo.get(
                    "owner",
                    {}).get(
                        "login",
                        "",
                    ),
                "description": repo.get(
                    "description"
                ) or "No description",

                "stars": repo.get(
                    "stargazers_count",
                    0,
                ),

                "forks": repo.get(
                    "forks_count",
                    0,
                ),

                "language": repo.get(
                    "language"
                ) or "N/A",

                "open_issues": repo.get(
                    "open_issues_count",
                    0,
                ),

                "url": repo.get(
                    "html_url",
                    "",
                ),

                "default_branch": repo.get(
                    "default_branch",
                    "main",
                ),

                "updated_at": repo.get(
                    "updated_at"
                ),

                "topics": repo.get(
                    "topics",
                    [],
                ),
            })

        return json.dumps({
            "type": "repositories",
            "query": query,
            "result_count": len(
                repositories
            ),
            "results": repositories,
        })

    except Exception as e:

        logger.error(
            f"❌ GitHub repository search error: {e}"
        )

        return json.dumps({
            "type": "repositories",
            "query": query,
            "result_count": 0,
            "results": [],
            "error": str(e),
        })


# ============================================================
# REPOSITORY INFORMATION
# ============================================================

@tool
def github_get_repo_info(
    owner: str,
    repo: str,
) -> str:
    """
    Get detailed information about a GitHub repository.

    Returns structured JSON.
    """

    logger.info(
        f"🔧 github_get_repo_info: "
        f"{owner}/{repo}"
    )

    try:
        with httpx.Client(timeout=15.0) as client:

            repo_resp = client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}",
                headers=_get_headers(),
            )

            repo_resp.raise_for_status()

            repo_data = repo_resp.json()

            lang_resp = client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/languages",
                headers=_get_headers(),
            )

            languages = (
                lang_resp.json()
                if lang_resp.status_code == 200
                else {}
            )

        repository = {
            "full_name": repo_data.get(
                "full_name",
                f"{owner}/{repo}",
            ),

            "description": repo_data.get(
                "description"
            ) or "No description",

            "stars": repo_data.get(
                "stargazers_count",
                0,
            ),

            "forks": repo_data.get(
                "forks_count",
                0,
            ),

            "watchers": repo_data.get(
                "subscribers_count",
                0,
            ),

            "language": repo_data.get(
                "language"
            ) or "N/A",

            "languages": list(
                languages.keys()
            ),

            "default_branch": repo_data.get(
                "default_branch",
                "main",
            ),

            "open_issues": repo_data.get(
                "open_issues_count",
                0,
            ),

            "license": (
                repo_data.get(
                    "license",
                    {}
                ).get(
                    "name",
                    "No license",
                )
                if repo_data.get("license")
                else "No license"
            ),

            "created_at": repo_data.get(
                "created_at"
            ),

            "updated_at": repo_data.get(
                "updated_at"
            ),

            "url": repo_data.get(
                "html_url",
                "",
            ),

            "clone_url": repo_data.get(
                "clone_url",
                "",
            ),
        }

        return json.dumps({
            "type": "repository",
            "repository": repository,
        })

    except Exception as e:

        logger.error(
            f"❌ GitHub repo info error: {e}"
        )

        return json.dumps({
            "type": "repository",
            "repository": None,
            "error": str(e),
        })


# ============================================================
# ISSUES
# ============================================================

@tool
def github_get_issues(
    owner: str,
    repo: str,
    state: str = "open",
    max_results: int = 5,
) -> str:
    """
    Get issues from a GitHub repository.

    Returns structured JSON.
    """

    logger.info(
        f"🔧 github_get_issues: "
        f"{owner}/{repo} ({state})"
    )

    try:
        params = {
            "state": state,
            "per_page": max_results,
            "sort": "updated",
        }

        with httpx.Client(timeout=15.0) as client:

            response = client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues",
                headers=_get_headers(),
                params=params,
            )

            response.raise_for_status()

            issues = response.json()

        results = []

        for issue in issues:

            labels = [
                label.get("name", "")
                for label in issue.get(
                    "labels",
                    [],
                )
            ]

            results.append({
                "number": issue.get(
                    "number",
                    0,
                ),

                "title": issue.get(
                    "title",
                    "Untitled issue",
                ),

                "state": issue.get(
                    "state",
                    state,
                ),

                "author": issue.get(
                    "user",
                    {},
                ).get(
                    "login",
                    "unknown",
                ),

                "labels": labels,

                "created_at": issue.get(
                    "created_at"
                ),

                "updated_at": issue.get(
                    "updated_at"
                ),

                "comments": issue.get(
                    "comments",
                    0,
                ),

                "url": issue.get(
                    "html_url",
                    "",
                ),
            })

        return json.dumps({
            "type": "issues",
            "repository": f"{owner}/{repo}",
            "state": state,
            "result_count": len(results),
            "results": results,
        })

    except Exception as e:

        logger.error(
            f"❌ GitHub issues error: {e}"
        )

        return json.dumps({
            "type": "issues",
            "repository": f"{owner}/{repo}",
            "state": state,
            "result_count": 0,
            "results": [],
            "error": str(e),
        })


# ============================================================
# PULL REQUESTS
# ============================================================

@tool
def github_get_pull_requests(
    owner: str,
    repo: str,
    state: str = "open",
    max_results: int = 5,
) -> str:
    """
    Get pull requests from a GitHub repository.

    Returns structured JSON.
    """

    logger.info(
        f"🔧 github_get_pull_requests: "
        f"{owner}/{repo} ({state})"
    )

    try:
        params = {
            "state": state,
            "per_page": max_results,
            "sort": "updated",
        }

        with httpx.Client(timeout=15.0) as client:

            response = client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls",
                headers=_get_headers(),
                params=params,
            )

            response.raise_for_status()

            prs = response.json()

        results = []

        for pr in prs:

            results.append({
                "number": pr.get(
                    "number",
                    0,
                ),

                "title": pr.get(
                    "title",
                    "Untitled pull request",
                ),

                "state": pr.get(
                    "state",
                    state,
                ),

                "author": pr.get(
                    "user",
                    {},
                ).get(
                    "login",
                    "unknown",
                ),

                "head_branch": pr.get(
                    "head",
                    {},
                ).get(
                    "ref",
                    "",
                ),

                "base_branch": pr.get(
                    "base",
                    {},
                ).get(
                    "ref",
                    "",
                ),

                "created_at": pr.get(
                    "created_at"
                ),

                "updated_at": pr.get(
                    "updated_at"
                ),

                "review_comments": pr.get(
                    "review_comments",
                    0,
                ),

                "comments": pr.get(
                    "comments",
                    0,
                ),

                "url": pr.get(
                    "html_url",
                    "",
                ),
            })

        return json.dumps({
            "type": "pull_requests",
            "repository": f"{owner}/{repo}",
            "state": state,
            "result_count": len(results),
            "results": results,
        })

    except Exception as e:

        logger.error(
            f"❌ GitHub PR error: {e}"
        )

        return json.dumps({
            "type": "pull_requests",
            "repository": f"{owner}/{repo}",
            "state": state,
            "result_count": 0,
            "results": [],
            "error": str(e),
        })


# ============================================================
# TOOL REGISTRY
# ============================================================

GITHUB_AGENT_TOOLS = [
    github_search_repos,
    github_get_repo_info,
    github_get_issues,
    github_get_pull_requests,
]


GITHUB_TOOL_MAP = {
    "github_search_repos": github_search_repos,
    "github_get_repo_info": github_get_repo_info,
    "github_get_issues": github_get_issues,
    "github_get_pull_requests": github_get_pull_requests,
}