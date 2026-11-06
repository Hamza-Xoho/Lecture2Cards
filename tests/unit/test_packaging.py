"""The installed package must carry the reviewer templates and note-type assets."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def files(root):
    return {path.relative_to(root): path.read_bytes()
            for path in root.rglob('*')
            if path.is_file() and '__pycache__' not in path.parts}


def test_packaged_templates_match_skill_copy():
    assert files(ROOT/'src/cards/templates/review') == files(ROOT/'.claude/skills/anki2/templates/review')


def test_packaged_assets_match_skill_copy():
    assert files(ROOT/'src/cards/assets/coldrecall-cloze') == files(ROOT/'.claude/skills/anki2/assets/coldrecall-cloze')
