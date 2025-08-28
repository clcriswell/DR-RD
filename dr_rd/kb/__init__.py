"""Lightweight knowledge base utilities."""

from .models import KBRecord, KBSource
from . import store, index

__all__ = ["KBRecord", "KBSource", "store", "index"]
