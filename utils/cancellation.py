import threading


class CancellationToken:
    """Simple cooperative cancellation token."""

    def __init__(self) -> None:
        self._ev = threading.Event()

    def cancel(self) -> None:
        """Signal cancellation."""
        self._ev.set()

    def is_set(self) -> bool:
        """Return True if cancellation requested."""
        return self._ev.is_set()

    def raise_if_cancelled(self) -> None:
        """Raise RuntimeError if token has been cancelled."""
        if self._ev.is_set():
            raise RuntimeError("cancelled")
