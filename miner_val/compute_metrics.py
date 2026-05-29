"""
Computes precision, recall, F1, and accuracy for the Exception Miner tool,
using the four validated files as ground truth.

Files:
  Positive set  (miner flagged): tool_validation_author1.csv / tool_validation_author2.csv
  Negative set  (miner clean):   no_antipattern_sample_author1.csv / no_antipattern_sample_author2.csv

Interpretation:
  TP  = positive-set row where validator says has_ap=Y (miner correctly flagged)
  FP  = positive-set row where validator says has_ap=N (miner false positive)
  TN  = negative-set row where validator says has_ap=N (miner correctly passed)
  FN  = negative-set row where validator says has_ap=Y (miner missed an AP)
"""

import pandas as pd

POS_A1 = "miner_val/tool_validation_author1.csv"
POS_A2 = "miner_val/tool_validation_author2.csv"
NEG_A1 = "miner_val/no_antipattern_sample_author1.csv"
NEG_A2 = "miner_val/no_antipattern_sample_author2.csv"


def metrics(tp, fp, tn, fn):
    total = tp + fp + tn + fn
    accuracy  = (tp + tn) / total if total else 0
    precision = tp / (tp + fp) if (tp + fp) else 0
    recall    = tp / (tp + fn) if (tp + fn) else 0
    f1        = (2 * precision * recall / (precision + recall)
                 if (precision + recall) else 0)
    return accuracy, precision, recall, f1


def evaluate(pos_df, neg_df, label):
    # skip NaN has_ap (rows that were never rated)
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


pos_a1 = pd.read_csv(POS_A1)
pos_a2 = pd.read_csv(POS_A2)
neg_a1 = pd.read_csv(NEG_A1)
neg_a2 = pd.read_csv(NEG_A2)

results = []
results.append(evaluate(pos_a1, neg_a1, "Author 1"))
results.append(evaluate(pos_a2, neg_a2, "Author 2"))

# CONSENSUS_MODE:
#   "agreement" — Y only when both raters agree on Y (inter-rater agreement view)
#   "union"     — Y if either rater says Y (conservative / pessimistic view of tool quality)
#
# Note: the two positive files may have different sizes (each author may have
# rated a different subset of rows).  The consensus is computed only on the
# rows that BOTH authors rated, joined on (project, file, function, anti_pattern).
# The two negative files are joined on (project, file, function).
CONSENSUS_MODE = "agreement"

# Join on the row index ("Unnamed: 0") rather than content-based keys to
# avoid cartesian-product blowup from rows that share the same
# (project, file, function, anti_pattern) but are genuinely distinct entries.
# Both files are guaranteed to have the same "Unnamed: 0" sequence.
POS_IDX = "Unnamed: 0"
NEG_KEYS = ["project", "file", "function"]

merged_pos = pd.merge(
    pos_a1[[POS_IDX, "anti_pattern", "has_ap"]].rename(columns={"has_ap": "has_ap_a1"}),
    pos_a2[[POS_IDX, "has_ap"]].rename(columns={"has_ap": "has_ap_a2"}),
    on=POS_IDX,
    how="inner",
)
merged_neg = pd.merge(
    neg_a1[NEG_KEYS + ["has_ap"]].rename(columns={"has_ap": "has_ap_a1"}),
    neg_a2[NEG_KEYS + ["has_ap"]].rename(columns={"has_ap": "has_ap_a2"}),
    on=NEG_KEYS,
    how="inner",
)

print(f"Rows rated by both authors — positive: {len(merged_pos)}, negative: {len(merged_neg)}")

if CONSENSUS_MODE == "agreement":
    merged_pos["has_ap"] = merged_pos.apply(
        lambda r: "Y" if r["has_ap_a1"] == r["has_ap_a2"] == "Y" else "N",
        axis=1,
    )
    merged_neg["has_ap"] = merged_neg.apply(
        lambda r: "Y" if r["has_ap_a1"] == r["has_ap_a2"] == "Y" else "N",
        axis=1,
    )
    consensus_label = "Consensus (agreement)"
else:
    merged_pos["has_ap"] = merged_pos.apply(
        lambda r: "Y" if r["has_ap_a1"] == "Y" or r["has_ap_a2"] == "Y" else "N",
        axis=1,
    )
    merged_neg["has_ap"] = merged_neg.apply(
        lambda r: "Y" if r["has_ap_a1"] == "Y" or r["has_ap_a2"] == "Y" else "N",
        axis=1,
    )
    consensus_label = "Consensus (union)"

results.append(evaluate(merged_pos, merged_neg, consensus_label))

# Summary table
summary = pd.DataFrame(results)[["label", "accuracy", "precision", "recall", "f1"]]
summary[["accuracy", "precision", "recall", "f1"]] = \
    summary[["accuracy", "precision", "recall", "f1"]].map(lambda x: f"{x*100:.2f}%")
print("=== Summary ===")
print(summary.to_string(index=False))
