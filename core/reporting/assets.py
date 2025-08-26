"""Static assets for HTML report exports."""

LIGHT_CSS = """
body { font-family: Arial, sans-serif; padding: 2rem; }
h1 { text-align: center; }
pre { white-space: pre-wrap; }
"""

DARK_CSS = """
body { font-family: Arial, sans-serif; padding: 2rem; background: #111; color: #eee; }
a { color: #9cf; }
pre { white-space: pre-wrap; }
"""


def get_css(theme: str = "light") -> str:
    return LIGHT_CSS if theme != "dark" else DARK_CSS
