"""Shared configuration values for the DR-RD project."""

from __future__ import annotations

import os


# Maximum number of tasks that can be executed in parallel. This can be
# overridden via the ``MAX_CONCURRENCY`` environment variable but defaults to 4
# to keep resource usage modest in most environments.
MAX_CONCURRENCY: int = int(os.getenv("MAX_CONCURRENCY", "4"))

