"""
Computes precision, recall, F1, and accuracy for the EH mechanism extraction
step, using the four validated CSV files as ground truth.

Inputs (filled by validators after manual inspection)
------------------------------------------------------
  Positive set  (miner detected a mechanism):
    eh_mechanisms_sample_author1.csv
    eh_mechanisms_sample_author2.csv

  Negative set  (miner detected nothing):
    eh_negative_sample_author1.csv
    eh_negative_sample_author2.csv

Confusion matrix mapping
------------------------
  Positive set, is_correct = Y  → TP  (miner correctly extracted the mechanism)
  Positive set, is_correct = N  → FP  (miner extracted a non-existing mechanism)
  Negative set, has_mechanism = N → TN  (miner correctly found nothing)
  Negative set, has_mechanism = Y → FN  (miner missed a real mechanism)

Usage
-----
  python3 eh_mechanisms_val/compute_precision.py

Run this only after both authors have completed their validation sheets.
For inter-rater agreement, use experiment_val/agreement.py as a reference.
"""

import sys

import pandas as pd

# ── file paths ────────────────────────────────────────────────────────────────
POS_A1 = "eh_mechanisms_val/eh_mechanisms_sample_author1.csv"
POS_A2 = "eh_mechanisms_val/eh_mechanisms_sample_author2.csv"
NEG_A1 = "eh_mechanisms_val/eh_negative_sample_author1.csv"
NEG_A2 = "eh_mechanisms_val/eh_negative_sample_author2.csv"


# ── helpers ───────────────────────────────────────────────────────────────────

def _load(path: str) -> pd.DataFrame:
    try:
        return pd.read_csv(path, low_memory=False)
    except FileNotFoundError:
        sys.exit(f"ERROR: file not found — {path}\nRun the build scripts first.")


def _metrics(tp: int, fp: int, tn: int, fn: int) -> tuple[float, float, float, float]:
    total     = tp + fp + tn + fn
    accuracy  = (tp + tn) / total          if total          else 0.0
    precision = tp / (tp + fp)             if (tp + fp)      else 0.0
    recall    = tp / (tp + fn)             if (tp + fn)      else 0.0
    f1        = (2 * precision * recall
                 / (precision + recall))   if (precision + recall) else 0.0
    return accuracy, precision, recall, f1


def _consensus(s1: pd.Series, s2: pd.Series, mode: str = "union") -> pd.Series:
    """
    Combine two raters into a consensus rating.
      union        — Y if *either* rater says Y  (pessimistic for the tool)
      intersection — Y only when *both* say Y     (optimistic for the tool)
    """
    if mode == "union":
        return (s1 == "Y") | (s2 == "Y")
    return (s1 == "Y") & (s2 == "Y")


def evaluate(
    label: str,
    pos_df: pd.DataFrame,
    neg_df: pd.DataFrame,
    pos_col: str = "is_correct",
    neg_col: str = "has_mechanism",
) -> None:
    """Print full metrics for one rater (or consensus)."""
    pos = pos_df.dropna(subset=[pos_col])
    neg = neg_df.dropna(subset=[neg_col])

    # skip blank strings (not yet filled)
    pos = pos[pos[pos_col].astype(str).str.strip().isin(["Y", "N"])]
    neg = neg[neg[neg_col].astype(str).str.strip().isin(["Y", "N"])]

    tp = (pos[pos_col].astype(str).str.strip() == "Y").sum()
    fp = (pos[pos_col].astype(str).str.strip() == "N").sum()
    tn = (neg[neg_col].astype(str).str.strip() == "N").sum()
    fn = (neg[neg_col].astype(str).str.strip() == "Y").sum()

    acc, prec, rec, f1 = _metrics(tp, fp, tn, fn)

    print(f"\n=== {label} ===")
    print(f"  Positive set: {len(pos)} rows  (TP={tp}, FP={fp})")
    print(f"  Negative set: {len(neg)} rows  (TN={tn}, FN={fn})")
    print(f"  Precision : {prec:.2%}")
    print(f"  Recall    : {rec:.2%}")
    print(f"  F1        : {f1:.2%}")
    print(f"  Accuracy  : {acc:.2%}")

    # Per-mechanism-type precision (positive set only)
    if "mechanism_type" in pos.columns:
        print("\n  Precision by mechanism type:")
        for mtype, grp in pos.groupby("mechanism_type"):
            g_tp = (grp[pos_col].astype(str).str.strip() == "Y").sum()
            g_fp = (grp[pos_col].astype(str).str.strip() == "N").sum()
            g_prec = g_tp / (g_tp + g_fp) if (g_tp + g_fp) else 0.0
            print(f"    {mtype:12s}: {g_prec:.2%}  (n={len(grp)}, TP={g_tp}, FP={g_fp})")


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    pos_a1 = _load(POS_A1)
    pos_a2 = _load(POS_A2)
    neg_a1 = _load(NEG_A1)
    neg_a2 = _load(NEG_A2)

    print("EH Mechanism Extraction — Precision / Recall / F1 / Accuracy")
    print("=" * 60)
    print(f"Positive set: {len(pos_a1)} rows  |  Negative set: {len(neg_a1)} rows")
    print(f"Total evaluated: {len(pos_a1) + len(neg_a1)} rows")

    # Per-rater evaluation
    evaluate("Author 1", pos_a1, neg_a1)
    evaluate("Author 2", pos_a2, neg_a2)

    # Consensus (agreement): Y only when both raters agree on Y — disagreements rated as N (FP)
    pos_con = pos_a1.copy()
    neg_con = neg_a1.copy()

    pos_a1_col = pos_a1["is_correct"].astype(str).str.strip()
    pos_a2_col = pos_a2["is_correct"].astype(str).str.strip()
    neg_a1_col = neg_a1["has_mechanism"].astype(str).str.strip()
    neg_a2_col = neg_a2["has_mechanism"].astype(str).str.strip()

    disagree_pos = (pos_a1_col != pos_a2_col).sum()
    disagree_neg = (neg_a1_col != neg_a2_col).sum()

    # positive set: Y only when both agree on Y → else N (disagreement = FP)
    pos_con["is_correct"]    = pos_a1_col.where(pos_a1_col == pos_a2_col, "N")
    # negative set: N only when both agree on N → else Y (disagreement = FN)
    neg_con["has_mechanism"] = neg_a1_col.where(neg_a1_col == neg_a2_col, "Y")

    print(f"\n--- Disagreements: {disagree_pos} positive (rated N/FP), {disagree_neg} negative rows (rated Y/FN) ---")

    evaluate("Consensus (agreement)", pos_con, neg_con)

    print("\n" + "=" * 60)
    print("Tip: resolve disagreements in both author files, then rerun.")


if __name__ == "__main__":
    main()
