import time

import pytest

from utils.timeouts import Deadline, with_deadline


def test_deadline_context_manager_times_out():
    deadline = Deadline(time.time() + 0.01)
    with pytest.raises(TimeoutError):
        with with_deadline(deadline):
            time.sleep(0.02)
