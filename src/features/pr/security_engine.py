"""Simple static security engine applying regex rules from config."""
import re
from typing import List, Dict
from src.shared.config import load_config


def run_security_engine(parsed_diff: List[Dict]) -> List[Dict]:
    findings = []
    cfg = load_config()
    rules = cfg.get("review", {}).get("security", {}).get("rules", [])
    for f in parsed_diff:
        path = f["path"]
        # naive: retrieve added lines
        for h in f.get("hunks", []):
            for line in h.get("lines", []):
                if not line.startswith("+"):
                    continue
                text = line[1:]
                for rule in rules:
                    pattern = rule.get("pattern")
                    if not pattern:
                        continue
                    if re.search(pattern, text):
                        findings.append({
                            "file": path,
                            "line": text,
                            "rule": rule.get("id"),
                            "description": rule.get("description"),
                            "severity": rule.get("severity", "medium"),
                        })
    return findings
