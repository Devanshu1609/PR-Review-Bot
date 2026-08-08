"""Top-level orchestration for the action."""
import os
import logging

from src.features.pr.handler import handle_pull_request
from src.features.push.handler import handle_merge

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    # Read tokens from environment
    github_token = os.getenv("GITHUB_TOKEN")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    # GitHub sets these environment variables in Actions
    event_name = os.getenv("GITHUB_EVENT_NAME")
    repo = os.getenv("GITHUB_REPOSITORY")
    if not repo:
        logger.error("GITHUB_REPOSITORY not set. Are you running inside Actions?")
        return

    owner, repo_name = repo.split("/")

    if event_name == "pull_request":
        # Expect GITHUB_REF or PR number in env; GitHub Actions exposes GITHUB_REF
        pr_number = os.getenv("PR_NUMBER")  # optional override for local testing
        if pr_number:
            pr_number = int(pr_number)
        else:
            # try to read from GITHUB_HEAD_REF? Not reliable; callers should provide PR_NUMBER for local runs
            logger.info("No PR_NUMBER provided; action expects to run inside GitHub with context.")
            return

        handle_pull_request(
            owner=owner,
            repo=repo_name,
            pr_number=pr_number,
            token=github_token,
        )
    elif event_name == "push":
        # On push (e.g., merged to main), run docs flow
        # For simplicity, expect env MERGED_PR_NUMBER for local testing
        merged_pr = os.getenv("MERGED_PR_NUMBER")
        if merged_pr:
            merged_pr = int(merged_pr)
            handle_merge(owner=owner, repo=repo_name, pr_number=merged_pr, token=github_token)
        else:
            logger.info("No merged PR number provided for push event. Exiting.")
    else:
        logger.info(f"Unsupported event: {event_name}. Exiting.")
