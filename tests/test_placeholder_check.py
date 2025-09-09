from dr_rd.evaluators.placeholder_check import evaluate


def test_placeholder_patterns_fail():
    assert evaluate("Material A")[0] is False
    assert evaluate({"url": "https://example.com/foo"})[0] is False
    assert evaluate("Research Journal X")[0] is False
    assert evaluate("Study Y")[0] is False


def test_realistic_strings_pass():
    data = {"name": "Aluminum", "source": "https://doi.org/10.1000/xyz"}
    assert evaluate(data)[0] is True


def test_materials_payload_placeholder_fails():
    payload = {
        "properties": [
            {
                "name": "Material A",
                "property": "density",
                "value": 1,
                "units": "g/cm3",
                "source": "https://example.com/x",
            }
        ]
    }
    assert evaluate(payload)[0] is False
