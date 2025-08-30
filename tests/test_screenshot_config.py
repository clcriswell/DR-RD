import yaml


def test_screenshot_config_keys():
    with open('docs/screenshots.yml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    assert 'pages' in config and isinstance(config['pages'], list)
    for page in config['pages']:
        for key in ('name', 'path', 'out'):
            assert key in page
