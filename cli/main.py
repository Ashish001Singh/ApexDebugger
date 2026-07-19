import sys
import json
import click
from src.apex_copilot.review import review
from src.apex_copilot.reasoning.models import Severity


@click.group()
def cli() -> None:
    """ApexDebugger — Salesforce Apex AI Code Reviewer."""


@cli.command()
@click.argument("file", type=click.Path(exists=True, readable=True))
@click.option("--json-output", is_flag=True, help="Output findings as JSON.")
@click.option("--min-severity", default="low", type=click.Choice(["low", "medium", "high"]))
def apex_review(file: str, json_output: bool, min_severity: str) -> None:
    """Review an Apex .cls FILE for issues."""
    with open(file) as f:
        code = f.read()

    result = review(code, filename=file)

    severity_order = {Severity.LOW: 0, Severity.MEDIUM: 1, Severity.HIGH: 2, Severity.INFO: -1}
    min_level = severity_order.get(Severity(min_severity), 0)
    filtered = [f for f in result.findings if severity_order.get(f.severity, 0) >= min_level]

    if json_output:
        click.echo(json.dumps([f.model_dump() for f in filtered], indent=2))
        return

    if not filtered:
        click.secho("No issues found.", fg="green")
        return

    click.echo(f"\nReviewing: {file}")
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

    has_high = any(f.severity == Severity.HIGH for f in filtered)
    sys.exit(1 if has_high else 0)


# Register command under expected name
cli.add_command(apex_review, name="review")
