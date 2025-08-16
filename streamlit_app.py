"""Deprecated stub: use `streamlit run app.py`. This routes to Lite profile."""
import os
from app import main

if __name__ == "__main__":  # pragma: no cover
    os.environ.setdefault("DRRD_DEFAULT_PROFILE", "Lite")
    main()
