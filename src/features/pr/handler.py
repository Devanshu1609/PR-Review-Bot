"""PR feature: orchestrates a pull request review."""
import logging
from typing import Optional

from src.features.pr.git_diff import parse_git_diff
from src.features.pr.cve_detection import check_vulnerabilities
from src.features.pr.security_engine import run_security_engine
from src.features.pr.llm_call import call_llm
from src.features.pr.octokit import (
    get_pr_context,
    load_state,
    post_review_comment,
)
from src.features.pr.compare_state import match_findings

logger = logging.getLogger(__name__)


def handle_pull_request(*, owner: str, repo: str, pr_number: int, token: Optional[str]):
    """Main handler called by the action entrypoint.

    This implementation is intentionally lightweight: it shows the control flow and uses
    helper modules for the real work.
    """
    if not token:
        raise RuntimeError("GITHUB token is required")

    # Load previous state from PR summary comment (if any)
    loaded_state = load_state(token, owner, repo, pr_number)

    # Fetch PR context including diff
    pr_context = get_pr_context(token, owner, repo, pr_number)
    raw_diff = pr_context.get("diff", "")
    pr_meta = {
        "title": pr_context.get("title"),
        "description": pr_context.get("description"),
        "commit_messages": pr_context.get("commit_messages", []),
    }

    parsed = parse_git_diff(raw_diff)
    if not parsed:
        logger.info("No files changed in PR. Skipping analysis.")
        return

    deps = check_vulnerabilities(parsed)
    security_findings = run_security_engine(parsed)
    llm_reviews = call_llm(parsed, security_findings, deps, pr_meta)

    fixed, matched = match_findings(llm_reviews, parsed, (loaded_state or {}).get("state", []))
    if not matched and not fixed:
        logger.info("No findings to report.")
        return

    summary = {
        "matched": matched,
        "fixed": fixed,
    }

    post_review_comment(token, owner, repo, pr_number, matched, fixed, summary, (loaded_state or {}).get("comment_id"))
