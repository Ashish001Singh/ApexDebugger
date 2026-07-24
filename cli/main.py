import sys
import json
import click
from pathlib import Path
from src.orchestrator.route import route
from src.orchestrator.synthesize import synthesize
from src.apex_copilot.review import review as apex_review_fn
from src.lwc_copilot.review import review as lwc_review_fn
from src.review_core.models import Severity


@click.group()
def cli() -> None:
    """ApexDebugger — Salesforce Apex AI Code Reviewer."""


@cli.command()
@click.option("--json-output", is_flag=True, help="Output findings as JSON.")
@click.option("--min-severity", default="low", type=click.Choice(["low", "medium", "high"]))
@click.argument("files", type=click.Path(exists=True, readable=True), nargs=-1, required=True)
def apex_review(files: tuple[str, ...], json_output: bool, min_severity: str) -> None:
    """Review one or more Apex .cls/.trigger or LWC .js FILES for issues."""
    paths = [Path(f) for f in files]
    routed = route(paths)
    
    for skipped in routed.skipped:
        click.secho(f"Skipping {skipped} — unrecognized extension.", fg="yellow")

    results = []
    for apex_path in routed.apex_files:
        results.append(apex_review_fn(apex_path.read_text(), filename=str(apex_path)))
    for bundle in routed.lwc_bundles:
        js = bundle.js.read_text()
        html = bundle.html.read_text() if bundle.html else ""
        results.append(lwc_review_fn(js, html, filename=str(bundle.js)))

    results = synthesize(results)

    severity_order = {Severity.LOW: 0, Severity.MEDIUM: 1, Severity.HIGH: 2, Severity.INFO: -1}
    min_level = severity_order.get(Severity(min_severity), 0)

    has_high = False
    for result in results:
        filtered = [f for f in result.findings if severity_order.get(f.severity, 0) >= min_level]

        if json_output:
            click.echo(json.dumps([f.model_dump() for f in filtered], indent=2))
            continue

        if not filtered:
            click.secho(f"{result.filename}: no issues found.", fg="green")
            continue

        click.echo(f"\nReviewing: {result.filename}")
        click.echo(f"Found {len(filtered)} issue(s):\n")

        for finding in filtered:
            color = {"high": "red", "medium": "yellow", "low": "cyan"}.get(finding.severity.value, "white")
            click.secho(
                f"  [{finding.severity.value.upper()}] Line {finding.line} — {finding.rule.value}",
                fg=color,
                bold=True,
            )
            click.echo(f"    {finding.message}")
            click.secho(f"    Fix: {finding.suggestion}", fg="blue")
            click.echo()

        if any(f.severity == Severity.HIGH for f in filtered):
            has_high = True

    sys.exit(1 if has_high else 0)


    # Register command under expected name
cli.add_command(apex_review, name="review")