"""Configuration loader for .mifoshawk.yml"""
import os
import yaml


def load_config(path: str = ".mifoshawk.yml"):
    # Prefer repository config in repo root; fall back to example shipped with action
    if os.path.exists(path):
        with open(path, "r") as f:
            return yaml.safe_load(f) or {}
    # try example
    example = os.path.join(os.path.dirname(__file__), "..", "..", ".mifoshawk.yml.example")
    if os.path.exists(example):
        with open(example, "r") as f:
            return yaml.safe_load(f) or {}
    return {}
