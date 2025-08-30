# Streamlit UI Research

- **Page config** sets title, icon, and layout for thin entry points using `st.set_page_config`.[Official docs](https://docs.streamlit.io/library/api-reference/utilities/st.set_page_config)
- **Multipage apps** place scripts under a `pages/` directory and can jump with `st.switch_page` for simple navigation.[Official docs](https://docs.streamlit.io/library/api-reference/navigation/st.switch_page)
- **Layout primitives** like `st.columns`, `st.tabs`, `st.expander`, and `st.form` arrange widgets while keeping orchestration logic elsewhere.[Official docs](https://docs.streamlit.io/library/api-reference/layout)
- **State management** relies on `st.session_state` and `st.query_params` to persist data and sync URLs without embedding business logic.[Official docs](https://docs.streamlit.io/library/api-reference/session-state)
- **Caching** with `st.cache_data` and `st.cache_resource` stores results and connections for faster, inexpensive reruns.[Official docs](https://docs.streamlit.io/library/advanced-features/caching)
- **Status elements** (`st.status`, `st.progress`, `st.spinner`, `st.toast`, `st.dialog`) give feedback for long tasks and errors.[Official docs](https://docs.streamlit.io/library/api-reference/status)
- **File IO** uses `st.file_uploader` and `st.download_button` for light uploads and exports tied to orchestrators.[Official docs](https://docs.streamlit.io/library/api-reference/widgets/st.file_uploader)
- **Data display** leverages `st.dataframe` and `st.data_editor` for tabular insights powered by backend adapters.[Official docs](https://docs.streamlit.io/library/api-reference/data/st.data_editor)
- **Theming** reads from `.streamlit/config.toml` to apply colors and fonts consistently.[Official docs](https://docs.streamlit.io/library/advanced-features/theming)
- **Accessibility** requires alt text, keyboard-friendly widgets, and avoiding color-only cues.[Official docs](https://docs.streamlit.io/library/api-reference/status/st.toast#accessibility)
- **Community Cloud deploy** uses `.streamlit/secrets.toml`, `requirements.txt`, and optional `packages.txt` for dependencies.[Official docs](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app)
