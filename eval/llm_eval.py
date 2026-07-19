import json, statistics
from pathlib import Path
from src.apex_copilot.review import review

GOLDEN = Path(__file__).parent / "golden_set.jsonl"
N_RUNS = 2          # eval repeats per case; voting (3x) already inside each review()
GATE_F1 = 0.7          # mean F1 must clear this

def score(expected: set[str], found: set[str]) -> dict:
    tp = len(expected & found)
    fp = len(found - expected)
    fn = len(expected - found)

    # ⚠️ EDGE CASE: division by zero. If tp+fp == 0 (found nothing),
    #    precision is undefined. Convention: define as ___ (0.0 or 1.0?).
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0

    # ⚠️ EDGE CASE: if P and R are both 0, F1 divides by zero too.
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {"precision": precision, "recall": recall, "f1": f1, "tp": tp, "fp": fp, "fn": fn}


def run_llm_eval():
    cases = [json.loads(l) for l in GOLDEN.read_text().splitlines() if l.strip()]

    for case in cases:
        expected = set(case["expected_rules"])
        f1_scores = []                                  # collect F1 across N runs

        for _ in range(N_RUNS):
            result = review(case["code"], case["id"])
            found = { f.rule.value for f in result.findings }   # <- BLANK 1
            s = score(expected, found)
            f1_scores.append(s["f1"])

        # aggregate the wobble
        mean_f1 = statistics.mean(f1_scores)
        spread  = max(f1_scores) - min(f1_scores) 
        status = "PASS" if mean_f1>= GATE_F1 else "FAIL"
        print(f"[{status}] {case['id']}: mean F1={mean_f1:.2f}  spread={spread:.2f}  runs={[f'{x:.2f}' for x in f1_scores]}")

if __name__ == "__main__":
    run_llm_eval()