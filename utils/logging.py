import logging
from core.privacy import redact_for_logging

logger = logging.getLogger("drrd")
logger.setLevel(logging.INFO)

h = logging.StreamHandler()
fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
h.setFormatter(fmt)
logger.addHandler(h)


def safe_exc(log, idea, msg, exc, request_id: str | None = None):
    from utils.search_tools import obfuscate_query

    base = f"{msg}: {exc}"
    if request_id:
        base = f"{base} [req={request_id}]"
    (log or logger).error(obfuscate_query("error", idea or "", base))


def _preview(raw: str | None) -> str:
    try:
        return str(redact_for_logging(raw or ""))[:256]
    except Exception:
        return (raw or "")[:256]


def log_self_check(run_id: str | None, support_id: str | None, result: dict, raw_head: str) -> None:
    logger.info(
        "self_check run_id=%s support_id=%s result=%s head=%r",
        run_id,
        support_id,
        result,
        _preview(raw_head),
    )


def log_dynamic_agent_failure(run_id: str | None, support_id: str | None, reason: str, raw_head: str) -> None:
    logger.warning(
        "dynamic_agent_failure run_id=%s support_id=%s reason=%s head=%r",
        run_id,
        support_id,
        reason,
        _preview(raw_head),
    )
