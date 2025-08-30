import threading
import time

import pytest

from utils.cancellation import CancellationToken


def test_cancellation_token_stops_loop():
    token = CancellationToken()

    def long_loop():
        for _ in range(1000):
            token.raise_if_cancelled()
            time.sleep(0.001)

    def cancel_later():
        time.sleep(0.01)
        token.cancel()

    t = threading.Thread(target=cancel_later)
    t.start()
    with pytest.raises(RuntimeError):
        long_loop()
    t.join()
