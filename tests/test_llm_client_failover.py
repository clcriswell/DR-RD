from types import SimpleNamespace

from utils import llm_client


class RateLimitError(Exception):
    pass


class AuthError(Exception):
    pass


def _noop(*a, **k):
    return None


def test_retry_on_rate_limit(monkeypatch):
    calls = {'n':0}
    def fake_call(prov, model, payload, stream=False):
        calls['n'] += 1
        if calls['n'] < 3:
            raise RateLimitError('rate limit')
        return {'ok': True}
    monkeypatch.setattr(llm_client, '_call_provider', fake_call)
    monkeypatch.setattr(llm_client, 'fallback_chain', lambda mode: [('p','m')])
    monkeypatch.setattr(llm_client, 'cache_get', lambda *a, **k: None)
    monkeypatch.setattr(llm_client, 'cache_put', _noop)
    monkeypatch.setattr(llm_client, 'status', lambda k: 'closed')
    monkeypatch.setattr(llm_client, 'record_failure', _noop)
    monkeypatch.setattr(llm_client, 'record_success', _noop)
    monkeypatch.setattr(llm_client, 'allow_half_open', lambda k: True)
    monkeypatch.setattr(llm_client, 'log_event', _noop)
    resp = llm_client.chat({'messages':[]}, mode='x')
    assert resp == {'ok': True}
    assert calls['n'] == 3


def test_fallback_on_auth(monkeypatch):
    calls = []
    def fake_call(prov, model, payload, stream=False):
        calls.append(prov)
        if prov == 'p1':
            raise AuthError('bad')
        return {'ok': True}
    monkeypatch.setattr(llm_client, '_call_provider', fake_call)
    monkeypatch.setattr(llm_client, 'fallback_chain', lambda mode: [('p1','m1'),('p2','m2')])
    monkeypatch.setattr(llm_client, 'cache_get', lambda *a, **k: None)
    monkeypatch.setattr(llm_client, 'cache_put', _noop)
    monkeypatch.setattr(llm_client, 'status', lambda k: 'closed')
    monkeypatch.setattr(llm_client, 'record_failure', _noop)
    monkeypatch.setattr(llm_client, 'record_success', _noop)
    monkeypatch.setattr(llm_client, 'allow_half_open', lambda k: True)
    monkeypatch.setattr(llm_client, 'log_event', _noop)
    resp = llm_client.chat({'messages':[]}, mode='x')
    assert resp == {'ok': True}
    assert calls == ['p1','p2']
