"""
Computes precision, recall, F1, and accuracy for the Exception Miner tool,
using the three validated files as ground truth.

Files:
  Positive set  (miner flagged): tool_validation_eric.csv / tool_validation_jairo.csv
  Negative set  (miner clean):   no_antipattern_sample_validated.csv

Interpretation:
  TP  = positive-set row where validator says has_ap=Y (miner correctly flagged)
  FP  = positive-set row where validator says has_ap=N (miner false positive)
  TN  = negative-set row where validator says has_ap=N (miner correctly passed)
  FN  = negative-set row where validator says has_ap=Y (miner missed an AP)
"""

import pandas as pd

ERIC_CSV   = "miner_val/tool_validation_eric.csv"
JAIRO_CSV  = "miner_val/tool_validation_jairo.csv"
NEG_CSV    = "miner_val/no_antipattern_sample_validated.csv"


def metrics(tp, fp, tn, fn):
    total = tp + fp + tn + fn
    accuracy  = (tp + tn) / total if total else 0
    precision = tp / (tp + fp) if (tp + fp) else 0
    recall    = tp / (tp + fn) if (tp + fn) else 0
    f1        = (2 * precision * recall / (precision + recall)
                 if (precision + recall) else 0)
    return accuracy, precision, recall, f1


def evaluate(pos_df, neg_df, label):
    # skip NaN has_ap (legacy rows that were never rated)
    pos = pos_df.dropna(subset=["has_ap"])
    neg = neg_df.dropna(subset=["has_ap"])

    tp = (pos["has_ap"] == "Y").sum()
    fp = (pos["has_ap"] == "N").sum()
    tn = (neg["has_ap"] == "N").sum()
    fn = (neg["has_ap"] == "Y").sum()

    acc, prec, rec, f1 = metrics(tp, fp, tn, fn)

    print(f"=== {label} ===")
    print(f"  Positive set rows : {len(pos)}  (TP={tp}, FP={fp})")
    print(f"  Negative set rows : {len(neg)}  (TN={tn}, FN={fn})")
    print(f"  Accuracy          : {acc:.4f}  ({acc*100:.2f}%)")
    print(f"  Precision         : {prec:.4f}  ({prec*100:.2f}%)")
    print(f"  Recall            : {rec:.4f}  ({rec*100:.2f}%)")
    print(f"  F1                : {f1:.4f}  ({f1*100:.2f}%)")
    print()

    # per-AP breakdown
    ap_stats = []
    for ap, grp in pos.groupby("anti_pattern"):
        ap_tp = (grp["has_ap"] == "Y").sum()
        ap_fp = (grp["has_ap"] == "N").sum()
        ap_prec = ap_tp / (ap_tp + ap_fp) if (ap_tp + ap_fp) else 0
        ap_stats.append((ap, ap_tp, ap_fp, ap_prec))

    ap_df = pd.DataFrame(ap_stats,
                         columns=["anti_pattern", "TP", "FP", "Precision"])
    ap_df = ap_df.sort_values("anti_pattern")
    print(f"  Per-anti-pattern precision:")
    print(ap_df.to_string(index=False))
    print()
    return {"label": label, "TP": int(tp), "FP": int(fp),
            "TN": int(tn), "FN": int(fn),
            "accuracy": acc, "precision": prec, "recall": rec, "f1": f1}


eric  = pd.read_csv(ERIC_CSV)
jairo = pd.read_csv(JAIRO_CSV)
neg   = pd.read_csv(NEG_CSV)

results = []
results.append(evaluate(eric,  neg, "Eric"))
results.append(evaluate(jairo, neg, "Jairo"))

# CONSENSUS_MODE:
#   "agreement" — Y only when both raters agree on Y (inter-rater agreement view)
#   "union"     — Y if either rater says Y (conservative / pessimistic view of tool quality)
CONSENSUS_MODE = "agreement"

merged = eric[["project", "file", "function", "anti_pattern", "has_ap"]].copy()
merged = merged.rename(columns={"has_ap": "has_ap_eric"})
merged["has_ap_jairo"] = jairo["has_ap"].values

if CONSENSUS_MODE == "agreement":
    merged["has_ap"] = merged.apply(
        lambda r: "Y" if r["has_ap_eric"] == r["has_ap_jairo"] == "Y" else "N",
        axis=1,
    )
    consensus_label = "Consensus (agreement)"
else:
    merged["has_ap"] = merged.apply(
        lambda r: "Y" if r["has_ap_eric"] == "Y" or r["has_ap_jairo"] == "Y" else "N",
        axis=1,
    )
    consensus_label = "Consensus (union)"

results.append(evaluate(merged, neg, consensus_label))

# Summary table
summary = pd.DataFrame(results)[["label", "accuracy", "precision", "recall", "f1"]]
summary[["accuracy","precision","recall","f1"]] = \
    summary[["accuracy","precision","recall","f1"]].map(lambda x: f"{x*100:.2f}%")
print("=== Summary ===")
print(summary.to_string(index=False))
