import streamlit as st


_A11Y_CSS = """
<style>
/* Focus visibility across common widgets */
:root { --focus-ring: 2px solid #0A63FF; }
button:focus-visible,
[role="button"]:focus-visible,
input:focus-visible,
textarea:focus-visible,
select:focus-visible {
  outline: var(--focus-ring) !important;
  outline-offset: 2px !important;
  box-shadow: none !important;
}
/* Larger hit targets for buttons and downloads */
.stButton button, .stDownloadButton button {
  min-height: 44px;
  padding: 10px 16px;
}
/* Respect reduced motion */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0s !important;
    transition-duration: 0s !important;
    scroll-behavior: auto !important;
  }
}
</style>
"""


def inject_accessibility_baseline():
    st.markdown(_A11Y_CSS, unsafe_allow_html=True)


def live_region_container():
    # screen reader polite announcements
    st.markdown(
        '<div aria-live="polite" aria-atomic="true" style="position:absolute;left:-9999px;height:1px;width:1px;overflow:hidden;"></div>',
        unsafe_allow_html=True,
    )

