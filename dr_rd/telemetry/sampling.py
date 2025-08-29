import random


def should_sample(rate: float) -> bool:
    if rate <= 0:
        return False
    if rate >= 1:
        return True
    return random.random() < rate
