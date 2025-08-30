import time
from pathlib import Path
from utils import circuit


def test_circuit_open_half_close(tmp_path, monkeypatch):
    monkeypatch.setattr(circuit, 'STATE', tmp_path / 'c.json')
    monkeypatch.setattr(circuit, 'WINDOW_SEC', 0.1)
    key = 'p:model'
    for _ in range(3):
        circuit.record_failure(key)
    assert circuit.status(key) == 'open'
    time.sleep(0.15)
    assert circuit.allow_half_open(key)
    assert circuit.status(key) == 'half'
    circuit.record_success(key)
    assert circuit.status(key) == 'closed'
