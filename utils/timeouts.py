import contextlib
import time


class Deadline:
    """Helper for absolute deadline timestamps."""

    def __init__(self, deadline_ts: float | None):
        self.deadline_ts = deadline_ts

    def remaining_ms(self) -> int | None:
        if self.deadline_ts is None:
            return None
        return max(0, int((self.deadline_ts - time.time()) * 1000))

    def expired(self) -> bool:
        ms = self.remaining_ms()
        return ms is not None and ms == 0


@contextlib.contextmanager
def with_deadline(deadline: 'Deadline'):
    if deadline and deadline.expired():
        raise TimeoutError("deadline reached")
    yield
    if deadline and deadline.expired():
        raise TimeoutError("deadline reached")
