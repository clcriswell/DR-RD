import json
from utils import flags


def test_missing_file_defaults_false(tmp_path, monkeypatch):
    path = tmp_path / 'flags.json'
    monkeypatch.setattr(flags, 'FLAGS_PATH', path)
    assert flags.is_enabled('foo') is False


def test_precedence(tmp_path, monkeypatch):
    path = tmp_path / 'flags.json'
    path.write_text(json.dumps({'version': 1, 'flags': {'foo': True}}))
    monkeypatch.setattr(flags, 'FLAGS_PATH', path)
    assert flags.is_enabled('foo') is True
    monkeypatch.setenv('FLAG_FOO', '0')
    assert flags.is_enabled('foo') is False
    assert flags.is_enabled('foo', params={'f_foo': '1'}) is True
