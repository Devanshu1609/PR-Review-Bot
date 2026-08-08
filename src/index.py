"""Top-level orchestration for the GitHub Action."""

import json
import logging
import os

from src.features.pr.handler import handle_pull_request
from src.features.push.handler import handle_merge


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_repository():
    repo = os.getenv("GITHUB_REPOSITORY")

    if not repo:
        raise RuntimeError("GITHUB_REPOSITORY is not set.")

    try:
        owner, repo_name = repo.split("/", 1)
    except ValueError:
        raise RuntimeError(
            f"Invalid GITHUB_REPOSITORY value: {repo}"
        )

    return owner, repo_name


def get_pr_number():
    """
    Get the pull request number from the GitHub event payload.
    """

    event_path = os.getenv("GITHUB_EVENT_PATH")

    if event_path and os.path.exists(event_path):
        try:
            with open(event_path, "r", encoding="utf-8") as f:
                event = json.load(f)

            pr_number = event.get("pull_request", {}).get("number")

            if pr_number:
                return int(pr_number)

        except (OSError, json.JSONDecodeError) as exc:
            logger.warning(
                "Could not read GitHub event payload: %s",
                exc,
            )

    # Fallback for manual/local testing
    pr_number = os.getenv("PR_NUMBER")

    if pr_number:
        return int(pr_number)

    return None


def main():
    github_token = os.getenv("GITHUB_TOKEN")
    event_name = os.getenv("GITHUB_EVENT_NAME")

    if not github_token:
        raise RuntimeError("GITHUB_TOKEN is not set.")

    owner, repo_name = get_repository()

    logger.info(
        "Running PR Review Bot for %s/%s",
        owner,
        repo_name,
    )

    logger.info(
        "GitHub event: %s",
        event_name,
    )

    if event_name == "pull_request":
        pr_number = get_pr_number()

        if not pr_number:
            logger.error(
                "Could not determine pull request number."
            )
            return

        logger.info(
            "Reviewing pull request #%s",
            pr_number,
        )

        handle_pull_request(
            owner=owner,
            repo=repo_name,
            pr_number=pr_number,
            token=github_token,
        )

    elif event_name == "push":
        merged_pr = os.getenv("MERGED_PR_NUMBER")

        if not merged_pr:
            logger.info(
                "No merged PR number provided for push event."
            )
            return

        handle_merge(
            owner=owner,
            repo=repo_name,
            pr_number=int(merged_pr),
            token=github_token,
        )

    else:
        logger.info(
            "Unsupported GitHub event: %s",
            event_name,
        )


if __name__ == "__main__":
    main()