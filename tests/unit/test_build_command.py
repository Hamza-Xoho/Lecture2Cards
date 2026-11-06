"""`cards build` owns the phase order; the agent only acts at pause prompts."""
import json
import os
import subprocess
import sys
from pathlib import Path

from cards import build

SOURCE = """Muscles of the Arm

Objectives
1. Identify muscles
2. Describe innervation

The biceps brachii originates from the supraglenoid tubercle.
"""


def cli(*args, cwd):
    env = {**os.environ, 'CARDS_BUILDS': str(Path(cwd) / 'builds')}
    return subprocess.run([sys.executable, '-m', 'cards', *map(str, args)],
                          capture_output=True, text=True, cwd=cwd, env=env)


def fixture(tmp_path):
    source = tmp_path / 'MED241_L015_arm.txt'
    source.write_text(SOURCE)
    made = cli('build', '--pdf', source, cwd=tmp_path)
    assert made.returncode == 0, made.stdout
    folder = next((tmp_path / 'builds').glob('*/build.json')).parent
    return folder, made


def state(build_dir):
    return json.loads((build_dir / 'build.json').read_text())


def test_build_pauses_at_p2_with_resume_command(tmp_path):
    folder, made = fixture(tmp_path)
    lines = made.stdout.splitlines()
    assert lines[0] == 'OK' and len(lines) <= 40 and len(made.stdout) <= 2000
    assert '⏸️  P2 Drafting' in made.stdout
    assert 'cards build --continue' in made.stdout
    assert str(folder / 'build.json') in made.stdout
    data = state(folder)
    assert data['phase'] == 'P2'
    assert [h['phase'] for h in data['history'] if h['status'] == 'done'] == ['P0', 'P1']
    assert data['history'][-1] == {**data['history'][-1], 'phase': 'P2', 'status': 'start'}


def test_build_continue_without_active_build_refuses(tmp_path):
    made = cli('build', '--continue', cwd=tmp_path)
    assert made.returncode == 3 and made.stdout.startswith('ERROR')


def test_build_done_build_is_not_replayed(tmp_path):
    folder, _ = fixture(tmp_path)
    data = state(folder)
    data['phase'] = 'done'
    (folder / 'build.json').write_text(json.dumps(data))
    made = cli('build', '--continue', '--build', folder, cwd=tmp_path)
    assert made.returncode == 0 and 'complete' in made.stdout


def test_review_scope_rules():
    log = {'conflicts': [{'id': 'n001'}], 'open_blockers': [], 'unresolved': [],
           'css_fix_needed': []}
    assert build.review_scope(None, 1, log) == (['n001'], False)
    wide = {'conflicts': [{'id': f'n00{i}'} for i in range(1, 5)], 'open_blockers': [],
            'unresolved': [], 'css_fix_needed': []}
    assert build.review_scope(None, 1, wide) == ([f'n00{i}' for i in range(1, 5)], True)
    blocker = {'conflicts': [], 'open_blockers': [{'note_id': 'n001'}], 'unresolved': [],
               'css_fix_needed': []}
    assert build.review_scope(None, 1, blocker) == ([], True)
    clean = {'conflicts': [], 'open_blockers': [], 'unresolved': [], 'css_fix_needed': []}
    assert build.review_scope(None, 1, clean) is None
    assert build.review_scope(None, 2, log) is None


def test_build_help_is_valid():
    made = cli('build', '--help', cwd=Path.cwd())
    assert made.returncode == 0 and '--pdf' in made.stdout and '--continue' in made.stdout