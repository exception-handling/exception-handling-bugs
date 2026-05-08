"""
Builds a stratified sample of 53 functions to replace the 'Unhandled Exception'
rows in tool_validation_eric.csv and tool_validation_jairo.csv.

Allocation (largest-remainder, n=53, proportional to paper population totals):
  Too Broad Except          22
  Swallowing Exceptions     15
  Too Broad Raising          9
  Bare Except Catch Block    6
  Nested Try-Except Blocks   1

Output: miner_val/ap_replacement_sample.csv
"""

import glob
import os

import pandas as pd

PARSER_DIR   = "output/parser/parser"
PROJECTS_CSV = "projects_py.csv"
ERIC_CSV     = "miner_val/tool_validation_eric.csv"
JAIRO_CSV    = "miner_val/tool_validation_jairo.csv"
OUTPUT_CSV   = "miner_val/ap_replacement_sample.csv"
RANDOM_SEED  = 42

ALLOCATION = {
    "Too Broad Except":         22,
    "Swallowing Exceptions":    15,
    "Too Broad Raising":         9,
    "Bare Except Catch Block":   6,
    "Nested Try-Except Blocks":  1,
}

AP_COL = {
    "Too Broad Except":          "n_generic_except",
    "Swallowing Exceptions":     "n_try_pass",
    "Too Broad Raising":         "n_captures_broad_raise",
    "Bare Except Catch Block":   "n_bare_except",
    "Nested Try-Except Blocks":  "n_nested_try",
}

# ── load valid projects ───────────────────────────────────────────────────────
valid_projects = set(pd.read_csv(PROJECTS_CSV)["name"].astype(str))

# ── load parser output ────────────────────────────────────────────────────────
frames = []
for csv_path in glob.glob(os.path.join(PARSER_DIR, "*_stats.csv")):
    project_name = os.path.basename(csv_path).replace("_stats.csv", "")
    if project_name not in valid_projects:
        continue
    df = pd.read_csv(csv_path)
    df.insert(0, "project", project_name)
    frames.append(df)

combined = pd.concat(frames, ignore_index=True)
print(f"Total rows from valid projects: {len(combined)}")

# ── build exclusion set (rows already in either validation file) ──────────────
eric  = pd.read_csv(ERIC_CSV)
jairo = pd.read_csv(JAIRO_CSV)
existing = pd.concat([eric, jairo], ignore_index=True)
exclude_keys = set(
    zip(existing["project"], existing["file"], existing["function"])
)
print(f"Rows to exclude (already validated): {len(exclude_keys)}")

mask_exclude = combined.apply(
    lambda r: (r["project"], r["file"], r["function"]) in exclude_keys, axis=1
)
pool = combined[~mask_exclude].copy()
print(f"Rows available after exclusion: {len(pool)}")

# ── stratified sampling ───────────────────────────────────────────────────────
sample_parts = []
for ap, n in ALLOCATION.items():
    col = AP_COL[ap]
    candidates = pool[pool[col] > 0]
    if len(candidates) < n:
        raise RuntimeError(
            f"Not enough candidates for '{ap}': need {n}, have {len(candidates)}"
        )
    drawn = candidates.sample(n=n, random_state=RANDOM_SEED)
    drawn = drawn[["project", "file", "function", "func_body"]].copy()
    drawn["anti_pattern"] = ap
    sample_parts.append(drawn)
    print(f"  {ap}: sampled {n} from {len(candidates)} candidates")

sample = pd.concat(sample_parts, ignore_index=True)
sample.to_csv(OUTPUT_CSV, index=False)
print(f"\nSaved {len(sample)} rows to {OUTPUT_CSV}")
