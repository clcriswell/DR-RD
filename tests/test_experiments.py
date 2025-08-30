import json
from collections import Counter

import json
from collections import Counter

from utils import experiments


def make_registry(tmp_path):
    path = tmp_path / 'experiments.json'
    data = {
        'version': 1,
        'experiments': {
            'exp1': {
                'variants': ['a', 'b'],
                'weights': [0.2, 0.8],
                'salt': 's',
            }
        },
    }
    path.write_text(json.dumps(data))
    return path


def test_deterministic_assignment(tmp_path, monkeypatch):
    reg = make_registry(tmp_path)
    monkeypatch.setattr(experiments, 'EXP_PATH', reg)
    v1 = experiments.assign('user', 'exp1')
    v2 = experiments.assign('user', 'exp1')
    assert v1 == v2


def test_weights_respected(tmp_path, monkeypatch):
    reg = make_registry(tmp_path)
    monkeypatch.setattr(experiments, 'EXP_PATH', reg)
    counts = Counter()
    for i in range(200):
        uid = f'u{i}'
        v, _ = experiments.assign(uid, 'exp1')
        counts[v] += 1
    frac = counts['a'] / 200
    assert 0.1 < frac < 0.3


def test_override_and_exposure(tmp_path, monkeypatch):
    reg = make_registry(tmp_path)
    monkeypatch.setattr(experiments, 'EXP_PATH', reg)
    assert experiments.force_from_params({'exp_exp1': 'b'}, 'exp1') == 'b'
    events = []
    experiments.exposure(events.append, 'user', 'exp1', 'a')
    assert events[0]['user_id'] != 'user'
    assert 'exp1' in events[0]['exp_id']
