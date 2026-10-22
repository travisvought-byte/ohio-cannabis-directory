"""Conservative path-only eligibility precheck. NOT an authorization to merge."""
import json
import sys

ALLOW = frozenset({
    "docs/README.md",
    "docs/CONTRIBUTING.md",
})
BLOCKED_SUFFIXES = (".py", ".js", ".cjs", ".yml", ".yaml", ".json", ".html")

def eligible(files):
    """Fail closed. A separate trusted gate must verify source, CI and approvals."""
    if not isinstance(files, list) or not files:
        return False
    for entry in files:
        if not isinstance(entry, dict):
            return False
        path, status = entry.get("filename"), entry.get("status")
        if not isinstance(path, str) or status != "modified":
            return False
        if path not in ALLOW or path.endswith(BLOCKED_SUFFIXES):
            return False
        if entry.get("previous_filename") is not None:
            return False
    return True

if __name__ == "__main__":
    try:
        payload = json.load(sys.stdin)
        ok = eligible(payload)
    except (ValueError, TypeError):
        ok = False
    print(json.dumps({"eligible_for_further_review": ok}))
    sys.exit(0 if ok else 1)
