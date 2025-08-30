from app.ui.copy import TEXT

REQUIRED_KEYS = [
    "welcome_title",
    "welcome_body",
    "run_help",
    "trace_empty_title",
    "trace_empty_body",
    "reports_empty_title",
    "reports_empty_body",
    "metrics_empty_title",
    "metrics_empty_body",
    "settings_help",
    "share_link_label",
]

def test_required_keys_present():
    for key in REQUIRED_KEYS:
        assert isinstance(TEXT.get(key), str) and TEXT[key]


def test_all_values_non_empty():
    for v in TEXT.values():
        assert isinstance(v, str) and v.strip()
