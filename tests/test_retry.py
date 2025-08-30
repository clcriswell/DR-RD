from utils.retry import backoff, should_retry


def test_backoff_monotonic():
    vals = [backoff(i, jitter=0.0) for i in range(1,5)]
    assert vals == sorted(vals)


def test_should_retry_truth_table():
    cases = {
        "rate_limit": True,
        "transient": True,
        "timeout": True,
        "auth": False,
        "quota": False,
        "validation": False,
        "unknown": False,
    }
    for k, v in cases.items():
        assert should_retry(k) is v
