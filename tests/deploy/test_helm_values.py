import yaml
from pathlib import Path


def test_flags_present():
    values = yaml.safe_load(Path('deploy/helm/dr-rd/values.yaml').read_text())
    flags = values.get('featureFlags', {})
    required = [
        'RAG_ENABLED',
        'ENABLE_LIVE_SEARCH',
        'EVALUATORS_ENABLED',
        'MODEL_ROUTING_ENABLED',
        'SAFETY_ENABLED',
        'PROVENANCE_ENABLED',
        'TELEMETRY_ENABLED',
    ]
    for key in required:
        assert key in flags
