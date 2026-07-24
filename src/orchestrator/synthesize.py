from src.review_core.models import ReviewResult, Severity

_SEVERITY_ORDER = {Severity.HIGH: 0, Severity.MEDIUM: 1, Severity.LOW: 2, Severity.INFO: 3}

def synthesize(results: list[ReviewResult]) -> list[ReviewResult]:
    for result in results:
        result.findings.sort(key=lambda f: _SEVERITY_ORDER.get(f.severity, 99))
    return results