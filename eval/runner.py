"""
Eval runner: loads golden_set.jsonl, runs review(), scores precision + recall.

Usage:
    uv run python eval/runner.py

Phase 1 gate: precision >= 0.8 AND recall >= 0.8 across all cases.
"""
import json
from pathlib import Path
from src.apex_copilot.review import review


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

    for case in cases:
        result = review(case["code"], filename=case["id"])
        found_rules = [f.rule for f in result.findings]
        precision, recall = score_case(case["expected_rules"], found_rules)
        total_precision += precision
        total_recall += recall

        status = "PASS" if precision >= GATE_PRECISION and recall >= GATE_RECALL else "FAIL"
        print(f"[{status}] {case['id']}")
        print(f"  Expected: {case['expected_rules']}")
        print(f"  Found:    {found_rules}")
        print(f"  Precision: {precision:.2f}  Recall: {recall:.2f}\n")

    avg_p = total_precision / len(cases)
    avg_r = total_recall / len(cases)
    overall = "PASS" if avg_p >= GATE_PRECISION and avg_r >= GATE_RECALL else "FAIL"
    print(f"{'='*50}")
    print(f"OVERALL [{overall}]  Avg Precision: {avg_p:.2f}  Avg Recall: {avg_r:.2f}")
    print(f"Gate: precision >= {GATE_PRECISION}, recall >= {GATE_RECALL}")

    if overall == "FAIL":
        raise SystemExit(1)


if __name__ == "__main__":
    run_eval()
