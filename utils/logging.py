import logging

logger = logging.getLogger("drrd")
logger.setLevel(logging.INFO)

h = logging.StreamHandler()
fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
h.setFormatter(fmt)
logger.addHandler(h)


def safe_exc(log, idea, msg, exc):
    from utils.search_tools import obfuscate_query

    (log or logger).error(obfuscate_query("error", idea or "", f"{msg}: {exc}"))
