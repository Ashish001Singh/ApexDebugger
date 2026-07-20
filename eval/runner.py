"""
Eval runner: loads golden_set.jsonl, runs review(), scores precision + recall.

Usage:
    uv run python eval/runner.py

Phase 1 gate: precision >= 0.8 AND recall >= 0.8 across all cases.
"""

"""
  Two evals, two jobs, two functions they call:
    runner.py    → run_all_rules  → "are my regex rules correct?"   (free, deterministic)
    llm_eval.py  → review         → "is the whole product good?"    (paid, probabilistic)
"""
import json
from pathlib import Path
from src.apex_copilot.rules import run_all_rules

REGEX_RULES = {"soql_in_loop","dml_in_loop","hardcoded_id","hardcoded_external_id",
               "missing_crud_fls","missing_sharing_declaration","explicit_system_mode",
               "nested_loop_2","nested_loop_deep"}

GOLDEN_SET = Path(__file__).parent / "golden_set.jsonl"
GATE_PRECISION = 0.8
GATE_RECALL = 0.8


def score_case(expected_rules: list[str], found_rules: list[str]) -> tuple[float, float]:
    expected = set(expected_rules)
    found = set(found_rules)
    tp = len(expected & found)
    precision = tp / len(found) if found else 0.0
    recall = tp / len(expected) if expected else 0.0
    return precision, recall


def run_eval() -> None:
    cases = [json.loads(line) for line in GOLDEN_SET.read_text().splitlines() if line.strip()]

    total_precision, total_recall = 0.0, 0.0
    print(f"\nRunning eval on {len(cases)} golden cases\n{'='*50}")
    graded = 0
    for case in cases:
        if not set(case["expected_rules"]) <= REGEX_RULES:
            continue
        graded += 1
        found_rules = [f.rule.value for f in run_all_rules(case["code"])]# regex only
        precision, recall = score_case(case["expected_rules"], found_rules)
        total_precision += precision
        total_recall += recall

        status = "PASS" if precision >= GATE_PRECISION and recall >= GATE_RECALL else "FAIL"
        print(f"[{status}] {case['id']}")
        print(f"  Expected: {case['expected_rules']}")
        print(f"  Found:    {found_rules}")
        print(f"  Precision: {precision:.2f}  Recall: {recall:.2f}\n")

    avg_p = total_precision / graded if graded else 0.0
    avg_r = total_recall / graded if graded else 0.0
    overall = "PASS" if avg_p >= GATE_PRECISION and avg_r >= GATE_RECALL else "FAIL"
    print(f"{'='*50}")
    print(f"OVERALL [{overall}]  Avg Precision: {avg_p:.2f}  Avg Recall: {avg_r:.2f}")
    print(f"Gate: precision >= {GATE_PRECISION}, recall >= {GATE_RECALL}")

    if overall == "FAIL":
        raise SystemExit(1)


if __name__ == "__main__":
    run_eval()
