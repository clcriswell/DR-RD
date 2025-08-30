from utils.env_snapshot import capture_env


def test_capture_env_has_expected_keys():
    snap = capture_env()
    assert "python_version" in snap
    assert "python_executable" in snap
    assert "platform" in snap
    assert "created_at" in snap
    assert isinstance(snap.get("packages"), dict)
    assert snap["packages"]
