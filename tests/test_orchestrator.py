from pathlib import Path
from src.orchestrator.route import route


def test_routes_apex_file(tmp_path):
    cls_file = tmp_path / "Foo.cls"
    cls_file.write_text("public class Foo {}")

    result = route([cls_file])

    assert result.apex_files == [cls_file]
    assert result.lwc_bundles == []
    assert result.skipped == []


def test_routes_lwc_bundle_with_html_sibling(tmp_path):
    bundle_dir = tmp_path / "myComponent"
    bundle_dir.mkdir()
    js_file = bundle_dir / "myComponent.js"
    html_file = bundle_dir / "myComponent.html"
    js_file.write_text("export default class MyComponent {}")
    html_file.write_text("<template></template>")

    result = route([js_file])

    assert result.apex_files == []
    assert len(result.lwc_bundles) == 1
    assert result.lwc_bundles[0].js == js_file
    assert result.lwc_bundles[0].html == html_file


def test_routes_lwc_js_without_html_sibling(tmp_path):
    js_file = tmp_path / "orphan.js"
    js_file.write_text("export default class Orphan {}")

    result = route([js_file])

    assert len(result.lwc_bundles) == 1
    assert result.lwc_bundles[0].html is None


def test_skips_unknown_extension(tmp_path):
    unknown_file = tmp_path / "notes.txt"
    unknown_file.write_text("hello")

    result = route([unknown_file])

    assert result.apex_files == []
    assert result.lwc_bundles == []
    assert result.skipped == [unknown_file]


from src.orchestrator.synthesize import synthesize
from src.review_core.models import ReviewResult, Finding, Severity


def _finding(rule, severity, line):
    return Finding(rule=rule, severity=severity, line=line, message="x", suggestion="y")


def test_synthesize_sorts_findings_by_severity_within_each_result():
    result = ReviewResult(
        filename="Foo.cls",
        findings=[
            _finding("missing_sharing_declaration", Severity.INFO, 1),
            _finding("dml_in_loop", Severity.HIGH, 5),
            _finding("nested_loop_2", Severity.MEDIUM, 3),
        ],
    )

    synthesized = synthesize([result])

    assert len(synthesized) == 1
    severities = [f.severity for f in synthesized[0].findings]
    assert severities == [Severity.HIGH, Severity.MEDIUM, Severity.INFO]


def test_synthesize_preserves_one_result_per_file():
    apex_result = ReviewResult(filename="Foo.cls", findings=[])
    lwc_result = ReviewResult(filename="bar.js", findings=[])

    synthesized = synthesize([apex_result, lwc_result])

    filenames = [r.filename for r in synthesized]
    assert filenames == ["Foo.cls", "bar.js"]
