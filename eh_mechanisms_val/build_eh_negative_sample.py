"""
Builds a random negative sample of 384 functions where the miner detected
NO exception handling mechanism, to complement the positive sample and allow
computing recall, F1, and accuracy alongside precision.

Context
-------
The positive sample (eh_mechanisms_sample_author*.csv) captures functions
where the miner DID detect a mechanism (positive predictions).  Validators
confirm whether each extracted snippet is correct → gives TP and FP.

This script captures functions where the miner detected NOTHING.  Validators
read the full function body and check whether any EH mechanism is actually
present but was missed → gives TN (correctly found nothing) and FN (miner
missed a real mechanism).

Negative pool
-------------
  Total functions in dataset/final_dataset/ :  1,295,543
  Functions with ≥1 detected mechanism      :    140,360
  Negative pool (all 4 count cols = 0)      :  1,155,183
  Sample size                               :        384

Validator columns to fill
--------------------------
  has_mechanism  — "N" if no EH mechanism found (TN),
                   "Y" if a mechanism the miner missed is found (FN)
  mechanism_found — if has_mechanism=Y, note which type(s):
                    try-except / raise / try-finally / try-else
  notes           — optional free-form comment

Outputs
-------
  eh_mechanisms_val/eh_negative_sample_author1.csv
  eh_mechanisms_val/eh_negative_sample_author2.csv
  (identical; each author works independently)
"""

import glob
import os
import sys

import pandas as pd

# ── configuration ─────────────────────────────────────────────────────────────
FINAL_DATASET_DIR = "dataset/final_dataset"
OUT_AUTHOR1       = "eh_mechanisms_val/eh_negative_sample_author1.csv"
OUT_AUTHOR2       = "eh_mechanisms_val/eh_negative_sample_author2.csv"
RANDOM_SEED       = 42
SAMPLE_SIZE       = 384

# All four mechanism-count columns must be 0 for a row to qualify
MECH_COLS = ["n_try_except", "n_raise", "n_finally", "n_try_else"]


# ── helpers ───────────────────────────────────────────────────────────────────

def shorten_path(path: str) -> str:
    """Strip the machine-specific prefix, keeping the project-relative path."""
    marker = os.sep + "projects" + os.sep + "py" + os.sep
    idx = path.find(marker)
    if idx != -1:
        return path[idx + len(marker):]
    return path


# ── load full dataset ─────────────────────────────────────────────────────────

def load_dataset() -> pd.DataFrame:
    csv_paths = sorted(glob.glob(os.path.join(FINAL_DATASET_DIR, "*_stats.csv")))
    if not csv_paths:
        sys.exit(f"ERROR: no CSVs found in {FINAL_DATASET_DIR!r}")

    frames: list[pd.DataFrame] = []
    for csv_path in csv_paths:
        project = os.path.basename(csv_path).replace("_stats.csv", "")
        df = pd.read_csv(csv_path, low_memory=False)
        df.insert(0, "project", project)
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)
    print(f"Loaded {len(combined):,} function rows from {len(frames)} projects")
    return combined


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print("Loading dataset …")
    combined = load_dataset()

    # Keep only rows where every mechanism count is 0
    mask_no_mech = (combined[MECH_COLS] == 0).all(axis=1)
    pool = combined[mask_no_mech].copy()
    print(f"Negative pool (all mechanism counts = 0): {len(pool):,} rows")

    if len(pool) < SAMPLE_SIZE:
        sys.exit(
            f"ERROR: not enough negative rows ({len(pool)}) to draw {SAMPLE_SIZE}"
        )

    # Uniform random sample
    sample = pool.sample(n=SAMPLE_SIZE, random_state=RANDOM_SEED)
    sample = sample[["project", "file", "function", "func_body"]].copy()
    sample = sample.reset_index(drop=True)
    sample.index = sample.index + 1   # 1-based id
    sample.index.name = "id"

    # Shorten absolute file paths
    sample["file"] = sample["file"].apply(shorten_path)

    # Blank validator columns
    sample["has_mechanism"]   = ""   # Y / N  (to be filled by validator)
    sample["mechanism_found"] = ""   # e.g. "try-except, raise" (fill if Y)
    sample["notes"]           = ""   # optional free-form comment

    output = sample.reset_index()    # bring 'id' back as column

    os.makedirs("eh_mechanisms_val", exist_ok=True)
    output.to_csv(OUT_AUTHOR1, index=False)
    output.to_csv(OUT_AUTHOR2, index=False)

    print(f"\nSaved {len(output)} rows to:")
    print(f"  {OUT_AUTHOR1}")
    print(f"  {OUT_AUTHOR2}")
    print(f"\nUnique projects in sample: {output['project'].nunique()}")
    print(
        "\nValidators: fill 'has_mechanism' (Y/N). "
        "If Y, note which type(s) in 'mechanism_found'."
    )


if __name__ == "__main__":
    main()
