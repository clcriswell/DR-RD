from __future__ import annotations

import json
import logging
import os


def _flag(name: str) -> bool:
    return os.getenv(name, "false").lower() == "true"


EVALUATORS_ENABLED = _flag("EVALUATORS_ENABLED")
PARALLEL_EXEC_ENABLED = _flag("PARALLEL_EXEC_ENABLED")
TOT_PLANNING_ENABLED = _flag("TOT_PLANNING_ENABLED")
REFLECTION_ENABLED = _flag("REFLECTION_ENABLED")
SIM_OPTIMIZER_ENABLED = _flag("SIM_OPTIMIZER_ENABLED")
SIM_OPTIMIZER_STRATEGY: str = os.getenv("SIM_OPTIMIZER_STRATEGY", "random")
SIM_OPTIMIZER_MAX_EVALS: int = int(os.getenv("SIM_OPTIMIZER_MAX_EVALS", "50"))
RAG_ENABLED = _flag("RAG_ENABLED")
RAG_TOPK: int = int(os.getenv("RAG_TOPK", "5"))
ENABLE_LIVE_SEARCH = _flag("ENABLE_LIVE_SEARCH")
LIVE_SEARCH_BACKEND: str = os.getenv("LIVE_SEARCH_BACKEND", "openai")
LIVE_SEARCH_MAX_CALLS: int = 3
LIVE_SEARCH_SUMMARY_TOKENS: int = 256
SERPAPI_KEY: str = os.getenv("SERPAPI_KEY", "")
ENABLE_IMAGES = _flag("ENABLE_IMAGES")
FAISS_INDEX_URI: str | None = os.getenv("FAISS_INDEX_URI")
FAISS_INDEX_DIR: str = os.getenv("FAISS_INDEX_DIR", ".faiss_index")
FAISS_BOOTSTRAP_MODE: str = os.getenv("FAISS_BOOTSTRAP_MODE", "download")
VECTOR_INDEX_PRESENT: bool = False
VECTOR_INDEX_PATH: str = ""
VECTOR_INDEX_SOURCE: str = "none"
VECTOR_INDEX_REASON: str = ""

EVALUATION_ENABLED = _flag("EVALUATION_ENABLED")
EVALUATION_MAX_ROUNDS: int = int(os.getenv("EVALUATION_MAX_ROUNDS", "1"))
EVALUATION_HUMAN_REVIEW = _flag("EVALUATION_HUMAN_REVIEW")
EVALUATION_USE_LLM_RUBRIC = _flag("EVALUATION_USE_LLM_RUBRIC")
EVAL_WEIGHTS = json.loads(
    os.getenv("EVAL_WEIGHTS", '{"clarity":0.3,"completeness":0.5,"grounding":0.2}')
)
EVAL_MIN_OVERALL: float = float(os.getenv("EVAL_MIN_OVERALL", "0.65"))

# Default evaluator weights and threshold. ``EVALUATOR_WEIGHTS`` can be
# overridden via an environment variable containing a JSON object.
EVALUATOR_WEIGHTS = json.loads(
    os.getenv(
        "EVALUATOR_WEIGHTS",
        '{"cost": 0.25, "feasibility": 0.35, "novelty": 0.25, "compliance": 0.15}',
    )
)
EVALUATOR_MIN_OVERALL: float = float(os.getenv("EVALUATOR_MIN_OVERALL", "0.6"))

# Parameters for Tree-of-Thoughts planning. These remain inexpensive to
# access even when the feature flag is disabled.
TOT_K: int = int(os.getenv("TOT_K", "3"))
TOT_BEAM: int = int(os.getenv("TOT_BEAM", "2"))
TOT_MAX_DEPTH: int = int(os.getenv("TOT_MAX_DEPTH", "2"))

# Reflection parameters
REFLECTION_PATIENCE: int = int(os.getenv("REFLECTION_PATIENCE", "2"))
REFLECTION_MAX_ATTEMPTS: int = int(os.getenv("REFLECTION_MAX_ATTEMPTS", "1"))


def get_env_defaults() -> dict:
    return {
        "PARALLEL_EXEC_ENABLED": PARALLEL_EXEC_ENABLED,
        "TOT_PLANNING_ENABLED": TOT_PLANNING_ENABLED,
        "TOT_K": TOT_K,
        "TOT_BEAM": TOT_BEAM,
        "TOT_MAX_DEPTH": TOT_MAX_DEPTH,
        "EVALUATORS_ENABLED": EVALUATORS_ENABLED,
        "EVALUATOR_MIN_OVERALL": (
            EVALUATOR_MIN_OVERALL if "EVALUATOR_MIN_OVERALL" in globals() else 0.0
        ),
        "REFLECTION_ENABLED": REFLECTION_ENABLED,
        "REFLECTION_PATIENCE": REFLECTION_PATIENCE,
        "RAG_ENABLED": RAG_ENABLED,
        "RAG_TOPK": RAG_TOPK,
        "ENABLE_LIVE_SEARCH": ENABLE_LIVE_SEARCH,
        "LIVE_SEARCH_BACKEND": LIVE_SEARCH_BACKEND,
        "LIVE_SEARCH_MAX_CALLS": LIVE_SEARCH_MAX_CALLS,
        "LIVE_SEARCH_SUMMARY_TOKENS": LIVE_SEARCH_SUMMARY_TOKENS,
        "ENABLE_IMAGES": ENABLE_IMAGES,
        "SIM_OPTIMIZER_ENABLED": SIM_OPTIMIZER_ENABLED,
        "SIM_OPTIMIZER_STRATEGY": SIM_OPTIMIZER_STRATEGY,
        "SIM_OPTIMIZER_MAX_EVALS": SIM_OPTIMIZER_MAX_EVALS,
        "EVALUATION_ENABLED": EVALUATION_ENABLED,
        "EVALUATION_MAX_ROUNDS": EVALUATION_MAX_ROUNDS,
        "EVALUATION_HUMAN_REVIEW": EVALUATION_HUMAN_REVIEW,
        "EVALUATION_USE_LLM_RUBRIC": EVALUATION_USE_LLM_RUBRIC,
        "EVAL_MIN_OVERALL": EVAL_MIN_OVERALL,
        "EVAL_WEIGHTS": EVAL_WEIGHTS,
    }


def apply_overrides(cfg: dict) -> None:
    """Apply config-driven overrides to module-level feature flags.
    Accepts keys aligned with config/modes.yaml (standard profile)."""
    global RAG_ENABLED, RAG_TOPK, ENABLE_LIVE_SEARCH
    global LIVE_SEARCH_BACKEND, LIVE_SEARCH_MAX_CALLS, LIVE_SEARCH_SUMMARY_TOKENS
    global FAISS_BOOTSTRAP_MODE, VECTOR_INDEX_PATH, FAISS_INDEX_URI, ENABLE_IMAGES
    global EVALUATION_ENABLED, EVALUATION_MAX_ROUNDS, EVALUATION_HUMAN_REVIEW
    global EVALUATION_USE_LLM_RUBRIC, EVAL_MIN_OVERALL, EVAL_WEIGHTS
    if "rag_enabled" in cfg:
        RAG_ENABLED = bool(cfg.get("rag_enabled"))
    if "rag_top_k" in cfg:
        RAG_TOPK = int(cfg.get("rag_top_k", RAG_TOPK))
    if "live_search_enabled" in cfg:
        ENABLE_LIVE_SEARCH = bool(cfg.get("live_search_enabled"))
    if "live_search_backend" in cfg:
        LIVE_SEARCH_BACKEND = str(cfg.get("live_search_backend") or LIVE_SEARCH_BACKEND)
    if "live_search_max_calls" in cfg:
        LIVE_SEARCH_MAX_CALLS = int(cfg.get("live_search_max_calls", LIVE_SEARCH_MAX_CALLS))
    if "live_search_summary_tokens" in cfg:
        LIVE_SEARCH_SUMMARY_TOKENS = int(
            cfg.get("live_search_summary_tokens", LIVE_SEARCH_SUMMARY_TOKENS)
        )
    if "faiss_bootstrap_mode" in cfg:
        FAISS_BOOTSTRAP_MODE = str(cfg.get("faiss_bootstrap_mode") or FAISS_BOOTSTRAP_MODE)
    if "faiss_index_local_dir" in cfg:
        VECTOR_INDEX_PATH = str(cfg.get("faiss_index_local_dir") or VECTOR_INDEX_PATH)
    if "faiss_index_uri" in cfg:
        FAISS_INDEX_URI = str(cfg.get("faiss_index_uri") or FAISS_INDEX_URI)
    if "enable_images" in cfg:
        ENABLE_IMAGES = bool(cfg.get("enable_images"))
    if "evaluation_enabled" in cfg:
        EVALUATION_ENABLED = bool(cfg.get("evaluation_enabled"))
    if "evaluation_max_rounds" in cfg:
        EVALUATION_MAX_ROUNDS = int(cfg.get("evaluation_max_rounds", EVALUATION_MAX_ROUNDS))
    if "evaluation_human_review" in cfg:
        EVALUATION_HUMAN_REVIEW = bool(cfg.get("evaluation_human_review"))
    if "evaluation_use_llm_rubric" in cfg:
        EVALUATION_USE_LLM_RUBRIC = bool(cfg.get("evaluation_use_llm_rubric"))
    if "evaluation_min_overall" in cfg:
        EVAL_MIN_OVERALL = float(cfg.get("evaluation_min_overall", EVAL_MIN_OVERALL))
    if "evaluation_weights" in cfg:
        try:
            EVAL_WEIGHTS = dict(cfg.get("evaluation_weights", EVAL_WEIGHTS))
        except Exception:
            pass


def apply_mode_overrides(cfg: dict) -> None:
    """Deprecated alias for :func:`apply_overrides`.

    config.feature_flags.apply_mode_overrides() is deprecated; use
    :func:`apply_overrides` instead. This alias will be removed in the next
    release.
    """
    logging.warning(
        "config.feature_flags.apply_mode_overrides() is deprecated; use apply_overrides(). "
        "This alias will be removed in the next release."
    )
    apply_overrides(cfg)


# DEPRECATED: retained for one release; not used by runtime
class _DeprecatedImagesDefault(dict):
    def __getitem__(self, key):  # pragma: no cover - compatibility shim
        logging.warning(
            "config.feature_flags.DISABLE_IMAGES_BY_DEFAULT is deprecated; use ENABLE_IMAGES instead."
        )
        return super().__getitem__(key)


DISABLE_IMAGES_BY_DEFAULT = _DeprecatedImagesDefault(
    {"standard": not ENABLE_IMAGES, "test": not ENABLE_IMAGES, "deep": not ENABLE_IMAGES}
)
