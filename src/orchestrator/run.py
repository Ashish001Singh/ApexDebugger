"""
Shared orchestration entrypoint used by both the CLI and the PR-review script.

Pipeline: route → review each file → resolve referenced controllers (free) →
correlate (derive cross-language findings) → synthesize (consolidate + sort).
"""
import re
from pathlib import Path

from src.orchestrator.route import route
from src.orchestrator.synthesize import synthesize
from src.orchestrator.correlate import correlate
from src.apex_copilot.review import review as apex_review_fn
from src.apex_copilot.rules import run_all_rules as run_apex_rules
from src.lwc_copilot.review import review as lwc_review_fn
from src.review_core.models import ReviewResult

_APEX_IMPORT = re.compile(r"@salesforce/apex/(\w+)\.\w+")


def resolve_controller_findings(
    lwc_bundles, existing_results: list[ReviewResult], repo_root: Path
) -> list[ReviewResult]:
    """
    For controllers an LWC imports but that AREN'T in the reviewed set, locate
    their <Controller>.cls under repo_root and run the REGEX layer only (free,
    deterministic) to surface their security findings — enough for correlate to
    flag a cross-language risk even when the PR only touched the LWC.
    """
    already = {Path(r.filename).stem for r in existing_results}
    wanted: set[str] = set()
    for bundle in lwc_bundles:
        wanted |= set(_APEX_IMPORT.findall(bundle.js.read_text()))
    wanted -= already

    extra: list[ReviewResult] = []
    seen: set[str] = set()
    for controller in wanted:
        for cls_path in repo_root.rglob(f"{controller}.cls"):
            if controller in seen:
                break
            seen.add(controller)
            findings = run_apex_rules(cls_path.read_text())
            extra.append(ReviewResult(filename=str(cls_path), findings=findings))
            break
    return extra


def review_paths(paths: list[Path], resolve_controllers_from: Path | None = None) -> list[ReviewResult]:
    """Run the full multi-language pipeline over `paths`, return consolidated results.

    If `resolve_controllers_from` is given (a repo root), controllers referenced by
    the LWCs but not among `paths` are regex-scanned from the repo so cross-language
    correlation works even when the PR didn't change the Apex file.
    """
    routed = route(paths)

    results: list[ReviewResult] = []
    for apex_path in routed.apex_files:
        results.append(apex_review_fn(apex_path.read_text(), filename=str(apex_path)))
    for bundle in routed.lwc_bundles:
        js = bundle.js.read_text()
        html = bundle.html.read_text() if bundle.html else ""
        results.append(lwc_review_fn(js, html, filename=str(bundle.js)))

    if resolve_controllers_from is not None:
        results += resolve_controller_findings(routed.lwc_bundles, results, resolve_controllers_from)

    lwc_sources = {str(b.js): b.js.read_text() for b in routed.lwc_bundles}
    cross = correlate(results, lwc_sources)
    if cross:
        results.append(ReviewResult(filename="(cross-language)", findings=cross))

    return synthesize(results)
