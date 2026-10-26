"""Reject agent output outside the explicitly authorized, research-only pilot."""
import argparse
import json
import os
from pathlib import Path
import re
import stat
import subprocess


def git(*args):
    return subprocess.check_output(['git', '-c', 'core.fsmonitor=false', '-c',
                                    'core.hooksPath=/dev/null', *args])


def check(task, bundle):
    assert set(bundle) == {'base_sha', 'issue', 'run_id', 'files', 'summary', 'limitations'}, 'Unexpected bundle fields'
    assert bundle['base_sha'] == task['base_sha'] and bundle['issue'] == task['issue'] and bundle['run_id'] == task['run_id'], 'Artifact identity mismatch'
    assert isinstance(bundle['files'], list) and 1 <= len(bundle['files']) <= 3, 'Expected 1–3 changed files'
    paths = set()
    total = 0
    for f in bundle['files']:
        assert set(f) == {'path', 'content'}, 'Unexpected file fields'
        p, content = f['path'], f['content']
        assert isinstance(p, str) and re.fullmatch(r'data/research/[A-Za-z0-9][A-Za-z0-9._-]*\.(json|md)', p) and '..' not in p, 'Not a research path'
        assert p in task['auth']['files'] and p not in paths, 'Unauthorized or duplicate path'
        paths.add(p)
        assert isinstance(content, str) and '\x00' not in content, 'Expected UTF-8 text'
        size = len(content.encode('utf-8'))
        assert 0 < size <= 100_000, 'File size limit'
        total += size
        if p.endswith('.json'):
            json.loads(content, parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s)))
    assert total <= 200_000, 'Total byte limit'
    assert isinstance(bundle['summary'], str) and len(bundle['summary']) <= 8000, 'Summary limit'
    assert isinstance(bundle['limitations'], list) and len(bundle['limitations']) <= 20 and all(isinstance(x, str) and len(x) <= 1000 for x in bundle['limitations']), 'Limitations limit'


def regular_path(p):
    for parent in p.parents:
        if parent == Path('.'):
            break
        assert not parent.is_symlink(), 'Symlink directory'
    if p.exists() or p.is_symlink():
        mode = p.lstat().st_mode
        assert stat.S_ISREG(mode) and not mode & 0o111, 'Not ordinary non-executable text'


def export(task, report):
    assert git('rev-parse', 'HEAD').decode().strip() == task['base_sha'], 'Agent committed or changed base'
    paths = set(git('diff', '--no-ext-diff', '--name-only', '-z', 'HEAD').decode().split('\x00'))
    paths.update(git('ls-files', '--others', '--exclude-standard', '-z').decode().split('\x00'))
    paths.discard('')
    assert report['status'] == 'completed', 'Model reported blocked; no PR will be delivered'
    files = []
    for name in sorted(paths):
        p = Path(name)
        assert name in task['auth']['files'], 'Out-of-scope change: ' + name
        regular_path(p)
        assert p.is_file(), 'Deletion is outside pilot scope'
        assert p.stat().st_size <= 100_000, 'File size limit'
        files.append({'path': name, 'content': p.read_text(encoding='utf-8')})
    bundle = {k: task[k] for k in ('base_sha', 'issue', 'run_id')}
    bundle.update(files=files, summary=report['summary'], limitations=report['limitations'])
    check(task, bundle)
    return bundle


def materialize(task, bundle):
    check(task, bundle)
    assert git('rev-parse', 'HEAD').decode().strip() == task['base_sha'], 'Wrong checkout'
    assert not git('status', '--porcelain'), 'Checkout is not clean'
    for f in bundle['files']:
        p = Path(f['path'])
        regular_path(p)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f['content'], encoding='utf-8')
        p.chmod(0o644)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['export', 'apply'])
    parser.add_argument('task')
    parser.add_argument('data')
    parser.add_argument('--output')
    args = parser.parse_args()
    task = json.loads(Path(args.task).read_text())
    data = json.loads(Path(args.data).read_text())
    if args.mode == 'apply':
        materialize(task, data)
    else:
        Path(args.output).write_text(json.dumps(export(task, data), ensure_ascii=False))


if __name__ == '__main__':
    main()
