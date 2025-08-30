from pathlib import Path

import streamlit as st

_CSS_PATH = Path(__file__).with_suffix("").parent / "static" / "a11y.css"
_INJECTED_KEY = "_a11y_injected"


def inject():
    if st.session_state.get(_INJECTED_KEY):
        return
    st.markdown(
        """
        <a href="#main" class="skip-link">Skip to main content</a>
        <div id="a11y-top"></div>
        """,
        unsafe_allow_html=True,
    )
    if _CSS_PATH.exists():
        st.markdown(
            f"<style>{_CSS_PATH.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True
        )
    st.session_state[_INJECTED_KEY] = True


def main_start():
    """Place once near the top of the page's main content."""
    st.markdown('<main id="main" tabindex="-1"></main>', unsafe_allow_html=True)


def aria_live_region(key: str = "live_status"):
    """Creates or returns an aria-live region id."""
    region_id = f"live_{key}"
    st.markdown(
        f'<div id="{region_id}" role="status" aria-live="polite" style="height:0;overflow:hidden;"></div>',
        unsafe_allow_html=True,
    )
    return region_id
