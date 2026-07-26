"""
Review the given changed files and print a Markdown report for a PR comment.

Usage: python scripts/review_pr.py File1.cls Component.js ...
Called by .github/workflows/pr-review.yml on changed .cls/.trigger/.js/.html files.

Routes through the full orchestrator, so the report covers Apex, LWC, AND the
cross-language security seam. Controllers referenced by a changed LWC but not
themselves changed are regex-scanned from the repo (free) so cross-language
findings still surface.
"""
import sys
from pathlib import Path

from src.orchestrator.run import review_paths
from src.review_core.models import ReviewResult

_SEV_ICON = {"high": "🔴", "medium": "🟡", "low": "🔵", "info": "⚪"}


def format_result(result: ReviewResult) -> str:
    
    if result.summary and not result.findings:
        return f"## 🔎 Summary\n\n{result.summary}"
    if not result.findings:
        return f"### `{result.filename}`\n\n✅ No issues found."

    lines = [f"### `{result.filename}`", ""]
    for fnd in result.findings:
        icon = _SEV_ICON.get(fnd.severity.value, "•")
        lines.append(f"- {icon} **{fnd.severity.value.upper()}** · line {fnd.line} · `{fnd.rule.value}`")
        lines.append(f"  {fnd.message}")
        if fnd.suggestion:
            lines.append(f"  _Fix:_ {fnd.suggestion}")
    if result.summary:
        lines += ["", f"> {result.summary}"]
    return "\n".join(lines)


def main() -> None:
    files = sys.argv[1:]
    if not files:
        print("_ApexDebugger: no reviewable files changed._")
        return

    results = review_paths([Path(f) for f in files], resolve_controllers_from=Path.cwd())
    with_findings = [r for r in results if r.findings or r.summary]

    if not with_findings:
        print("## 🔎 ApexDebugger review\n\n✅ No issues found in the changed files.")
        return

    blocks = [format_result(r) for r in with_findings]
    print("## 🔎 ApexDebugger review\n\n" + "\n\n---\n\n".join(blocks))


if __name__ == "__main__":
    main()
