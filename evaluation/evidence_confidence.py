def score_confidence(findings: list, sources: list, quotes: list) -> float:
    # simple heuristic: coverage of findings, source count, presence of quotes
    base = 0.3 if findings else 0.0
    base += min(len(sources), 5) * 0.1
    if quotes:
        base += 0.2
    return max(0.0, min(1.0, base))
