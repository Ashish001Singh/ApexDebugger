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
from src.apex_copilot.rules import run_all_rules as run_apex_rules
from src.lwc_copilot.rules.registry import run_all_rules as run_lwc_rules

APEX_REGEX_RULES = {"soql_in_loop","dml_in_loop","hardcoded_id","hardcoded_external_id",
               "missing_crud_fls","missing_sharing_declaration","explicit_system_mode",
               "nested_loop_2","nested_loop_deep"}

LWC_REGEX_RULES = {"unsafe_inner_html", "manual_dom_manipulation",
                   "imperative_apex_no_error_handling", "missing_wire_error_handler",
                   "apex_call_in_loop"}

GOLDEN_SET = Path(__file__).parent / "golden_set.jsonl"
GATE_PRECISION = 0.8
GATE_RECALL = 0.8


def score_case(expected_rules, found_rules):
    expected = set(expected_rules)
    found = set(found_rules)
    if not expected:                      # negative case: success = found nothing
        precision = 1.0 if not found else 0.0
        recall = 1.0
        return precision, recall
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
        lang = case.get("lang", "apex")
        regex_rules = APEX_REGEX_RULES if lang == "apex" else LWC_REGEX_RULES
        if not set(case["expected_rules"]) <= regex_rules:
            continue
        graded += 1
        if lang == "apex":
            found_rules = [f.rule.value for f in run_apex_rules(case["code"])]# regex only
        else:
            found_rules = [f.rule.value for f in run_lwc_rules(case.get("js", ""), case.get("html", ""))]# regex only
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
