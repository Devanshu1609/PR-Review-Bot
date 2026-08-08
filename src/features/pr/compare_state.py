"""Simple matching of findings to identify new, active, and fixed items.

This module provides a tiny deterministic matcher for use in tests and the basic flow.
"""
from typing import List, Dict, Tuple


def match_findings(llm_reviews: List[Dict], parsed_diff: List[Dict], previous_state: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """Return (fixed, matched) where matched are current findings and fixed are items present previously but not now.

    This naive implementation treats the LLM reviews list as the current set of findings.
    """
    prev_set = {str(p) for p in previous_state or []}
    curr_set = {str(r) for r in llm_reviews or []}

    matched = [r for r in llm_reviews if str(r) in curr_set]
    fixed = [p for p in (previous_state or []) if str(p) not in curr_set]
    return fixed, matched
