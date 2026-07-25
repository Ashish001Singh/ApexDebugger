from src.review_core.models import ReviewResult, Severity,Finding
_SEVERITY_ORDER = {Severity.HIGH: 0, Severity.MEDIUM: 1, Severity.LOW: 2, Severity.INFO: 3}


def synthesize(results: list[ReviewResult]) -> list[ReviewResult]:
    # 1. dedup across all results by (filename, rule, line)
    seen: dict[tuple, "Finding"] = {}
    for r in results:
        for f in r.findings:
            key = (r.filename, f.rule, f.line)
            if key in seen:
                if key in seen:
                    if f.message not in seen[key].message:
                        seen[key].message += f"\n{f.message}"
            else:
                seen[key] = f

    # 2. regroup surviving findings back under their filename
    grouped: dict[str, list] = {r.filename: [] for r in results}
    for (filename, _, _), f in seen.items():
        grouped[filename].append(f)

    # 3. one ReviewResult per filename, findings sorted by severity
    out = []
    for filename, findings in grouped.items():
        findings.sort(key=lambda f: _SEVERITY_ORDER.get(f.severity, 99))      # BLANK 2: same severity sort as before
        out.append(ReviewResult(filename=filename, findings=findings))
    return out