"""
Review the given Apex files and print a Markdown report for a PR comment.

Usage: python scripts/review_pr.py File1.cls File2.cls
Called by .github/workflows/pr-review.yml on changed .cls/.trigger files.
"""
import sys
from src.apex_copilot.review import review

_SEV_ICON = {"high": "🔴", "medium": "🟡", "low": "🔵", "info": "⚪"}


def format_file(path: str) -> str:
    with open(path) as f:
        code = f.read()
    result = review(code, filename=path)

    if not result.findings:
        return f"### `{path}`\n\n✅ No issues found."

    lines = [f"### `{path}`", ""]
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
        print("_ApexDebugger: no Apex files changed._")
        return
    blocks = [format_file(p) for p in files]
    print("## 🔎 ApexDebugger review\n\n" + "\n\n---\n\n".join(blocks))


if __name__ == "__main__":
    main()
