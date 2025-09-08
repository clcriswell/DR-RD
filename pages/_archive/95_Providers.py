import streamlit as st

from app.ui.a11y import aria_live_region, inject, main_start
from utils import prefs, providers
from utils.telemetry import log_event
from utils.validate_providers import quick_probe


def _table_data():
    rows = []
    for prov, info in providers.available_providers().items():
        secret = "✅" if providers.has_secrets(prov) else "⚠️"
        for model in info.get("models", {}):
            price = providers.model_price(prov, model)
            rows.append(
                {
                    "Provider": prov,
                    "Secret": secret,
                    "Model": model,
                    "In $/1k": price.get("input_per_1k", 0.0),
                    "Out $/1k": price.get("output_per_1k", 0.0),
                }
            )
    return rows


def main():
    inject()
    main_start()
    aria_live_region()
    log_event({"event": "providers_page_view"})
    st.title("Providers & Models")

    rows = _table_data()
    st.dataframe(rows, hide_index=True)

    prefs_data = prefs.load_prefs()
    sel = providers.from_prefs_snapshot(
        prefs_data.get("defaults", {}).get("provider_model", {})
    ) or providers.default_model_for_mode("standard")
    cur_provider, cur_model = sel

    prov = st.selectbox(
        "Provider",
        list(providers.available_providers().keys()),
        index=list(providers.available_providers().keys()).index(cur_provider),
    )
    models = list(providers.list_models(prov).keys())
    model_idx = models.index(cur_model) if cur_model in models else 0
    mdl = st.selectbox("Model", models, index=model_idx)

    status = st.empty()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Validate"):
            result = quick_probe(prov, mdl)
            log_event(
                {
                    "event": "provider_validated",
                    "provider": prov,
                    "model": mdl,
                    "status": result.get("status"),
                }
            )
            status.write(result.get("status"))
    with col2:
        if st.button("Save as default"):
            snap = providers.to_prefs_snapshot(prov, mdl)
            prefs_data["defaults"]["provider_model"] = snap
            prefs.save_prefs(prefs_data)
            log_event({"event": "provider_default_changed", "provider": prov, "model": mdl})
            status.success("Saved")

    st.caption(
        "Orchestrators read this selection by default; runs may override via mode or advanced settings."
    )


if __name__ == "__main__":
    main()
