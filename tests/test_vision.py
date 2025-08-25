from dr_rd.tools import analyze_image, analyze_video


def test_analyze_image_returns_dict_without_deps():
    res = analyze_image(b"", ["ocr"])
    assert isinstance(res, dict)


def test_analyze_video_missing_file_or_dep():
    res = analyze_video("nonexistent.mp4", 1, ["detect"])
    assert "error" in res
