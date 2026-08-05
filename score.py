"""
Scores either answer set (run1_answers.py or run2_answers.py) against the
retrieved context produced by pipeline.py, using ROUGE-L F1, and runs a
paired bootstrap comparison of each enhanced condition against the
baseline.

Usage:
    python score.py run1
    python score.py run2
"""
import sys
import json
import csv
import importlib
import numpy as np
from rouge_score import rouge_scorer

def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "run1"
    mod = importlib.import_module(f"{which}_answers")
    ANSWERS = mod.ANSWERS

    scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
    d = json.load(open("prudence_retrieved.json"))

    rows = []
    for i, r in enumerate(d):
        gold = r["gold_answer"]
        for cond in ["C0", "C1", "C6"]:
            pred = ANSWERS[i][cond]
            f1 = scorer.score(gold, pred)["rougeL"].fmeasure
            rows.append({
                "condition": cond,
                "financebench_id": r["financebench_id"],
                "question_type": r["question_type"],
                "question": r["question"],
                "gold_answer": gold,
                "predicted_answer": pred,
                "rouge_f1": round(f1, 4),
            })

    out_path = f"results_{which}_rescored.csv"
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    import collections
    by_cond = collections.defaultdict(list)
    for row in rows:
        by_cond[row["condition"]].append(row["rouge_f1"])

    print(f"Mean ROUGE-L F1 by condition ({which}):")
    for cond in ["C0", "C1", "C6"]:
        vals = by_cond[cond]
        print(f"  {cond}: n={len(vals)}, mean={np.mean(vals):.4f}")

    rng = np.random.default_rng(42)
    c0 = np.array(by_cond["C0"])
    c1 = np.array(by_cond["C1"])
    c6 = np.array(by_cond["C6"])
    n = len(c0)
    n_boot = 10000

    def paired_bootstrap(a, b):
        diffs = a - b
        obs_mean = diffs.mean()
        boot_means = np.empty(n_boot)
        for i in range(n_boot):
            idx = rng.integers(0, n, n)
            boot_means[i] = diffs[idx].mean()
        lo, hi = np.percentile(boot_means, [2.5, 97.5])
        return obs_mean, lo, hi

    print("\nPaired bootstrap vs. baseline, 10000 resamples, 95% CI:")
    for name, arr in [("C1 (semantic) - C0", c1), ("C6 (hybrid) - C0", c6)]:
        obs, lo, hi = paired_bootstrap(arr, c0)
        sig = "significant" if (lo > 0 or hi < 0) else "not significant"
        print(f"  {name}: diff={obs:+.4f}, 95% CI=[{lo:+.4f}, {hi:+.4f}] -> {sig}")

if __name__ == "__main__":
    main()
