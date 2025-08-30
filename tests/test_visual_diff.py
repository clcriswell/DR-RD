from pathlib import Path

from PIL import Image

from scripts.visual_diff import diff_ratio, compute_diffs


def _make_image(path: Path, color: str) -> None:
    img = Image.new('RGB', (50, 50), color=color)
    img.save(path)


def test_diff_ratio_and_threshold(tmp_path):
    baseline_dir = tmp_path / 'baseline'
    candidate_dir = tmp_path / 'candidate'
    out_dir = tmp_path / 'out'
    baseline_dir.mkdir()
    candidate_dir.mkdir()

    base = baseline_dir / 'sample.png'
    cand = candidate_dir / 'sample.png'

    _make_image(base, 'white')
    _make_image(cand, 'white')
    # change a 5x5 area
    with Image.open(cand) as img:
        for x in range(5):
            for y in range(5):
                img.putpixel((x, y), (0, 0, 0))
        img.save(cand)

    ratio = diff_ratio(str(base), str(cand))
    assert abs(ratio - 0.01) < 0.001

    results, exceeds = compute_diffs(str(baseline_dir), str(candidate_dir), str(out_dir), 0.02)
    assert results[0].status == 'ok'
    assert not exceeds

    results, exceeds = compute_diffs(str(baseline_dir), str(candidate_dir), str(out_dir), 0.005)
    assert results[0].status == 'changed'
    assert exceeds
