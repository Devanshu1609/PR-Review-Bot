"""Basic pytest stubs for core modules."""
from src.features.pr.git_diff import parse_git_diff


def test_parse_empty():
    assert parse_git_diff("") == []


def test_parse_small_diff():
    diff = """diff --git a/foo.py b/foo.py
index e69de29..4b825dc 100644
--- a/foo.py
+++ b/foo.py
@@ -0,0 +1,2 @@
+print(1)
+print(2)
"""
    parsed = parse_git_diff(diff)
    assert len(parsed) == 1
    assert parsed[0]["path"].endswith("foo.py")
