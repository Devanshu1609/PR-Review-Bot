"""GitHub API helpers using httpx and PyGithub where convenient.

This module provides small, testable wrappers for the operations the action needs:
- get_pr_context: fetch diff, title, description
- load_state: find the summary comment and parse JSON state
- post_review_comment: create/update summary comment and optionally create review comments

The implementations are synchronous for simplicity.
"""
import os
import json
import logging
from typing import Optional, Dict, Any, List
import httpx
from github import Github
from dotenv import load_dotenv

load_dotenv()  # Load .env if present for local testing

logger = logging.getLogger(__name__)
STATE_MARKER = "PR-REVIEW-AGENT: STATE"


def _auth_headers(token: str):
    return {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}


def get_pr_context(token: str, owner: str, repo: str, pr_number: int) -> Dict[str, Any]:
    """Fetch PR metadata including the raw unified diff.

    Returns dict with keys: diff (string), title, description, commit_messages
    """
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = _auth_headers(token).copy()
    # Request diff
    headers_diff = headers.copy()
    headers_diff["Accept"] = "application/vnd.github.v3.diff"
    r = httpx.get(api_url, headers=headers_diff, timeout=30)
    diff_text = r.text if r.status_code == 200 else ""

    # Basic metadata
    headers_json = headers.copy()
    headers_json["Accept"] = "application/vnd.github.v3+json"
    r2 = httpx.get(api_url, headers=headers_json, timeout=10)
    meta = r2.json() if r2.status_code == 200 else {}
    title = meta.get("title")
    body = meta.get("body")

    # commit messages
    commits_url = meta.get('commits_url')
    commit_messages = []
    if commits_url:
        rc = httpx.get(commits_url, headers=headers_json, timeout=10)
        if rc.status_code == 200:
            commits = rc.json()
            for c in commits:
                commit_messages.append(c.get('commit', {}).get('message'))

    return {"diff": diff_text, "title": title, "description": body, "commit_messages": commit_messages}


def load_state(
    token: str,
    owner: str,
    repo: str,
    pr_number: int
) -> Optional[Dict[str, Any]]:
    """Find the summary comment containing the state marker and return parsed JSON state.

    Returns:
        {'comment_id': id, 'state': [...]}
        or None if no valid state is found.
    """

    g = Github(token)
    repository = g.get_repo(f"{owner}/{repo}")
    pr = repository.get_pull(pr_number)
    comments = pr.get_issue_comments()

    for c in comments:
        body = c.body or ""

        if STATE_MARKER not in body:
            continue

        try:
            # Get everything after the state marker.
            marker_index = body.index(STATE_MARKER)
            json_part = body[
                marker_index + len(STATE_MARKER):
            ].strip()

            # Remove the closing HTML comment marker.
            if "-->" in json_part:
                json_part = json_part.split("-->", 1)[0].strip()

            # Handle fenced JSON if present.
            if json_part.startswith("```"):
                lines = json_part.splitlines()

                # Remove opening ```json / ```
                if lines:
                    lines = lines[1:]

                # Remove closing ```
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]

                json_part = "\n".join(lines).strip()

            data = json.loads(json_part)

            return {
                "comment_id": c.id,
                "state": data,
            }

        except (json.JSONDecodeError, ValueError, TypeError) as exc:
            logger.warning(
                "Failed to parse state JSON from comment %s: %s",
                c.id,
                exc,
            )
            continue

        except Exception:
            logger.exception(
                "Unexpected error while loading state from comment %s",
                c.id,
            )
            continue

    return None


def post_review_comment(
    token: str,
    owner: str,
    repo: str,
    pr_number: int,
    matched: List[Dict],
    fixed: List[Dict],
    summary: Dict,
    existing_comment_id: Optional[int],
):
    """Create or update the PR summary comment.

    The visible part is GitHub-flavored Markdown.
    The agent state is stored inside an HTML comment so it is
    invisible to users but can still be loaded on the next run.
    """

    g = Github(token)
    repository = g.get_repo(f"{owner}/{repo}")
    pr = repository.get_pull(pr_number)

    # --------------------------------------------------------------
    # Build visible Markdown comment
    # --------------------------------------------------------------

    body = "## 🤖 AI PR Review\n\n"

    body += (
        f"Found **{len(matched)} active findings** "
        f"and **{len(fixed)} fixed issues**.\n\n"
    )

    # --------------------------------------------------------------
    # Active findings
    # --------------------------------------------------------------

    if matched:
        body += "### Findings\n\n"

        for finding in matched:
            file = finding.get("file", "(unknown file)")
            issue = finding.get("issue", "").strip()
            severity = finding.get("severity", "").strip()

            body += f"#### `{file}`"

            if severity:
                body += f" — **{severity}**"

            body += "\n\n"

            # IMPORTANT:
            # Add the issue itself, NOT the whole dictionary.
            body += issue + "\n\n"

    else:
        body += "### Findings\n\n"
        body += "No active findings. 🎉\n\n"

    # --------------------------------------------------------------
    # Fixed findings
    # --------------------------------------------------------------

    if fixed:
        body += "### Fixed Issues\n\n"

        for finding in fixed:
            file = finding.get("file", "(unknown file)")
            issue = finding.get("issue", "").strip()

            body += f"- **`{file}`**"

            if issue:
                body += f": {issue}"

            body += "\n"

        body += "\n"

    # --------------------------------------------------------------
    # Hidden state
    # --------------------------------------------------------------
    #
    # Do NOT put the JSON directly in the visible comment.
    #
    # GitHub will hide everything between <!-- and -->.
    #
    # load_state() can still read this information.
    # --------------------------------------------------------------

    state_json = json.dumps(summary)

    body += (
        f"<!-- {STATE_MARKER}\n"
        f"{state_json}\n"
        f"-->\n"
    )

    # --------------------------------------------------------------
    # Update existing comment
    # --------------------------------------------------------------

    if existing_comment_id:
        try:
            for comment in pr.get_issue_comments():
                if comment.id == existing_comment_id:
                    comment.edit(body)

                    logger.info("Updated existing summary comment")
                    return

            raise RuntimeError(
                f"Could not find issue comment with ID {existing_comment_id}"
            )

        except Exception:
            logger.exception(
                "Failed to update existing comment; creating a new one"
            )

    # --------------------------------------------------------------
    # Create new comment
    # --------------------------------------------------------------

    pr.create_issue_comment(body)

    logger.info("Posted summary comment")
