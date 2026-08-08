"""Dependency extraction and OSV vulnerability checks."""
import re
from typing import List, Dict
import httpx

OSV_API = "https://api.osv.dev/v1/query"


def extract_python_deps_from_requirements(content: str) -> List[Dict]:
    deps = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # very naive parsing: pkg==version
        m = re.match(r"([^=<>!~]+)==?([0-9a-zA-Z\.\-]*)", line)
        if m:
            deps.append({"name": m.group(1).strip(), "version": m.group(2).strip()})
    return deps


async def _query_osv(name: str, version: str):
    async with httpx.AsyncClient() as client:
        payload = {"package": {"name": name, "ecosystem": "PyPI"}, "version": version}
        r = await client.post(OSV_API, json=payload, timeout=10)
        return r.json()


def check_vulnerabilities(parsed_diff: List[Dict]) -> List[Dict]:
    """Scan changed files for dependency updates and query OSV.

    This is a synchronous, lightweight implementation that looks for changes to files named requirements.txt
    and returns a best-effort list of findings. For speed and testability this function does not call OSV here.
    """
    findings = []
    for f in parsed_diff:
        if f["path"].endswith("requirements.txt"):
            # join hunk lines to reconstruct added lines
            for h in f.get("hunks", []):
                for line in h.get("lines", []):
                    if line.startswith("+"):
                        text = line[1:]
                        deps = extract_python_deps_from_requirements(text)
                        for d in deps:
                            findings.append({"file": f["path"], "dependency": d})
    return findings
