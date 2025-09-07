from __future__ import annotations

from typing import Optional

from .api_call_log import APICallLogger

_api_call_logger: Optional[APICallLogger] = None


def set_api_call_logger(logger: APICallLogger | None) -> None:
    global _api_call_logger
    _api_call_logger = logger


def get_api_call_logger() -> APICallLogger | None:
    return _api_call_logger
