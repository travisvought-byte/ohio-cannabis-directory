"""Generate the trusted Codex profile used by execution and credential-free CI."""
import json
from pathlib import Path
import sys


def configuration(domains):
    config = '''web_search = "live"
[features]
network_proxy = true
[permissions.research]
extends = ":read-only"
[permissions.research.filesystem]
"/opt/codex-runner" = "read"
[permissions.research.filesystem.":workspace_roots"]
"data/research" = "write"
[permissions.research.network]
enabled = true
[permissions.research.network.domains]
'''
    return config + ''.join(json.dumps(d) + ' = "allow"\n' for d in domains)


if __name__ == '__main__':
    task = json.loads(Path(sys.argv[1]).read_text())
    Path(sys.argv[2]).write_text(configuration(task['auth']['domains']))
