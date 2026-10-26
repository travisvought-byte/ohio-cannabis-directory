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
status=0
CODEX_HOME="$smoke_dir/home" codex sandbox --permission-profile research --cd "$smoke_dir/work" -- python3 -c '
from pathlib import Path
import errno
Path("data/research/result.json").write_text("[]")
assert Path("README.md").read_text() == "protected baseline\n"
for name in ("README.md", ".github/forbidden.yml", ".git/config", "data/forbidden.json"):
    try:
        Path(name).write_text("forbidden")
    except OSError as error:
        if error.errno in (errno.EACCES, errno.EPERM, errno.EROFS):
            continue
        raise
    raise AssertionError("Sandbox allowed protected write: " + name)
print("PASS pinned CLI: research writes allowed; source, workflows and Git metadata protected")
' > "$smoke_dir/sandbox.log" 2>&1 || status=$?
cat "$smoke_dir/sandbox.log"
if [ "$status" -ne 0 ]; then
    python - "$smoke_dir/sandbox.log" <<'PY'
from pathlib import Path
import sys
message = Path(sys.argv[1]).read_text()[-5000:]
message = message.replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
print('::error title=Codex permission smoke failure::' + message)
PY
    exit "$status"
fi
test -s "$smoke_dir/work/data/research/result.json"
