from pathlib import Path


def test_build_guide_exists():
    assert Path('docs/build_guide.md').exists()


def test_appendices_present():
    assert Path('docs/appendices').exists()


def test_reproducibility_script_or_target():
    makefile_text = Path('Makefile').read_text() if Path('Makefile').exists() else ''
    script_exists = Path('scripts/reproduce.sh').exists()
    assert script_exists or 'reproduc' in makefile_text
