from dr_rd.evaluators.placeholder_check import evaluate


def test_placeholder_patterns_fail():
    assert evaluate("Material A")[0] is False
    assert evaluate({"url": "https://example.com/foo"})[0] is False
    assert evaluate("Research Journal X")[0] is False
    assert evaluate("Study Y")[0] is False


def test_realistic_strings_pass():
    data = {
        "name": "Aluminum",
        "source": "https://doi.org/10.1000/xyz"
    }
    assert evaluate(data)[0] is True
