from src.review_core.models import Finding
from collections import Counter


def vote_findings(runs: list[list[Finding]], threshold: int) -> list[Finding]:
    """
    runs = N independent LLM finding-lists. Keep one representative Finding per
    RULE that appears in >= threshold of the runs. Kills random hallucinations.
    """
    rule_votes = Counter()          # how many runs contain each rule
    representative = {}             # first Finding object seen per rule

    for run in runs:
        seen_this_run = set()
        for f in run:
            if f.rule not in representative:
                representative[f.rule] = f      # keep a real Finding to return
            seen_this_run.add(f.rule)           # dedupe within the run
        for rule in seen_this_run:
            rule_votes[rule] += 1               # one vote per run per rule

    return [representative[rule] for rule, votes in rule_votes.items() if votes >= threshold]