#!/usr/bin/env bash
# No model/provider request: exercise the actual pinned CLI's command sandbox.
set -euo pipefail
repo_root="$PWD"
smoke_dir=$(mktemp -d)
trap 'rm -rf "$smoke_dir"' EXIT
mkdir -p "$smoke_dir/home" "$smoke_dir/work/data/research" "$smoke_dir/work/.github"
chmod 700 "$smoke_dir/home"
printf '%s\n' '{"auth":{"domains":[]}}' > "$smoke_dir/task.json"
python "$repo_root/scripts/codex_research_config.py" "$smoke_dir/task.json" "$smoke_dir/home/config.toml"
git -C "$smoke_dir/work" init -q
printf '%s\n' 'protected baseline' > "$smoke_dir/work/README.md"
CODEX_HOME="$smoke_dir/home" codex sandbox --permission-profile research --cd "$smoke_dir/work" -- python3 -c '
from pathlib import Path
Path("data/research/result.json").write_text("[]")
assert Path("README.md").read_text() == "protected baseline\n"
for name in ("README.md", ".github/forbidden.yml", ".git/config", "data/forbidden.json"):
    try:
        Path(name).write_text("forbidden")
    except PermissionError:
        continue
    raise AssertionError("Sandbox allowed protected write: " + name)
print("PASS pinned CLI: research writes allowed; source, workflows and Git metadata protected")
'
test -s "$smoke_dir/work/data/research/result.json"
