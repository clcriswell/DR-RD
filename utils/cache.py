import streamlit as st


def cached_data(ttl: int = 15, show_spinner: bool = False):
    """Wrapper around st.cache_data with sane defaults."""
    return st.cache_data(ttl=ttl, show_spinner=show_spinner)


def cached_resource():
    """Wrapper around st.cache_resource."""
    return st.cache_resource
