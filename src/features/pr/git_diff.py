"""Utilities to parse unified git diffs into structured objects."""
from unidiff import PatchSet
from io import StringIO
from typing import List, Dict


def parse_git_diff(raw_diff: str) -> List[Dict]:
    """Parse a unified git diff string and return a list of changed files with hunks.

    Each file dict contains: path, is_binary, hunks (with added/removed lines and line numbers)
    """
    if not raw_diff:
        return []

    patch = PatchSet(StringIO(raw_diff))
    results = []
    for patched_file in patch:
        file_info = {
            "path": patched_file.path,
            "is_binary": patched_file.is_binary_file,
            "hunks": [],
        }
        for hunk in patched_file:
            h = {
                "source_start": hunk.source_start,
                "target_start": hunk.target_start,
                "lines": [str(l) for l in hunk],
            }
            file_info["hunks"].append(h)
        results.append(file_info)
    return results
