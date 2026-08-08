"""Matching of findings to identify active and fixed items."""

from typing import List, Dict, Tuple, Any


def _normalize_finding(finding: Any) -> Dict:
    """Convert a finding into the dictionary format used by the PR comment."""

    if isinstance(finding, dict):
        return finding

    if isinstance(finding, str):
        return {
            "file": "(multiple)",
            "issue": finding,
            "severity": "info",
        }

    return {
        "file": "(unknown file)",
        "issue": str(finding),
        "severity": "info",
    }


def _finding_key(finding: Dict) -> str:
    """Create a stable key for comparing findings."""

    return str(
        (
            finding.get("file", ""),
            finding.get("issue", ""),
            finding.get("severity", ""),
        )
    )


def match_findings(
    llm_reviews: List[Dict],
    parsed_diff: List[Dict],
    previous_state: List[Dict],
) -> Tuple[List[Dict], List[Dict]]:
    """
    Return (fixed, matched).

    matched:
        Current findings detected by the review.

    fixed:
        Findings that existed in the previous state but are no
        longer present in the current review.

    All returned findings are normalized to dictionaries.
    """

    current_findings = [
        _normalize_finding(finding)
        for finding in (llm_reviews or [])
    ]

    previous_findings = [
        _normalize_finding(finding)
        for finding in (previous_state or [])
    ]

    current_keys = {
        _finding_key(finding)
        for finding in current_findings
    }

    previous_keys = {
        _finding_key(finding)
        for finding in previous_findings
    }

    matched = current_findings

    fixed = [
        finding
        for finding in previous_findings
        if _finding_key(finding) not in current_keys
    ]

    return fixed, matched