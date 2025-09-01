"""Run page for the DR-RD Streamlit application."""

import importlib
import sys

# When this file is executed via ``streamlit run app.py`` it is loaded as the
# module ``app`` which shadows the real ``app`` package. Drop this module from
# ``sys.modules`` so that importing ``app`` loads the package instead of this
# file.
sys.modules.pop("app", None)

main = importlib.import_module("app").main

if __name__ in ("__main__", "app"):
    main()
