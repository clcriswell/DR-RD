from pathlib import Path

from utils import profiles


def _patch_root(tmp_path: Path, monkeypatch):
    root = tmp_path / "profiles"
    monkeypatch.setattr(profiles, "ROOT", root)
    root.mkdir(parents=True, exist_ok=True)


def test_save_list_load_apply(tmp_path, monkeypatch):
    _patch_root(tmp_path, monkeypatch)
    profiles.save("fast", {"mode": "standard", "budget_limit_usd": 0.5})
    lst = profiles.list_profiles()
    assert lst and lst[0].name == "fast"
    obj = profiles.load("fast")
    cfg = {"mode": "", "budget_limit_usd": None, "idea": "x"}
    merged = profiles.apply_to_config(cfg, obj)
    assert merged["mode"] == "standard"
    assert merged["budget_limit_usd"] == 0.5
    assert merged["idea"] == "x"


def test_update_clamp_delete(tmp_path, monkeypatch):
    _patch_root(tmp_path, monkeypatch)
    profiles.save("fast", {"mode": "standard", "max_tokens": 100})
    profiles.update("fast", {"max_tokens": 0, "budget_limit_usd": -5})
    obj = profiles.load("fast")
    assert obj["defaults"]["max_tokens"] == 1
    assert obj["defaults"]["budget_limit_usd"] == 0.0
    assert profiles.delete("fast") is True
    assert not (profiles.ROOT / "fast.json").exists()


def test_safe_name(tmp_path, monkeypatch):
    _patch_root(tmp_path, monkeypatch)
    profiles.save("My Profile!!", {})
    assert (profiles.ROOT / "my-profile-.json").exists()
    loaded = profiles.load("My Profile!!")
    assert loaded["name"] == "my-profile-"
