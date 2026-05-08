"""
Builds a random sample of 385 functions with NO exception handling anti-patterns
from the miner output, restricted to projects listed in projects_py.csv.

Output: miner_val/no_antipattern_sample.csv  (columns: project, file, function, func_body)
"""

import os
import glob
import pandas as pd

PARSER_DIR = "output/parser/parser"
PROJECTS_CSV = "projects_py.csv"
OUTPUT_CSV = "miner_val/no_antipattern_sample.csv"
SAMPLE_SIZE = 385
RANDOM_SEED = 42

AP_COLUMNS = [
    "n_try_pass",
    "n_generic_except",
    "n_captures_broad_raise",
    "n_captures_try_except_raise",
    "n_captures_misplaced_bare_raise",
    "n_bare_except",
    "n_bare_raise_finally",
]

# Step 1: valid project names
projects_df = pd.read_csv(PROJECTS_CSV)
valid_projects = set(projects_df["name"].astype(str))

# Step 2: load only output CSVs whose project name is in valid_projects
frames = []
for csv_path in glob.glob(os.path.join(PARSER_DIR, "*_stats.csv")):
    basename = os.path.basename(csv_path)
    project_name = basename.replace("_stats.csv", "")
    if project_name not in valid_projects:
        continue
    df = pd.read_csv(csv_path)
    df.insert(0, "project", project_name)
    frames.append(df)

if not frames:
    raise RuntimeError(f"No matching output CSVs found under {PARSER_DIR}")

combined = pd.concat(frames, ignore_index=True)
print(f"Total functions from valid projects: {len(combined)}")

# Step 3: keep only rows where every anti-pattern column is 0
no_ap = combined[(combined[AP_COLUMNS] == 0).all(axis=1)]
print(f"Functions with no anti-pattern: {len(no_ap)}")

if len(no_ap) < SAMPLE_SIZE:
    raise RuntimeError(
        f"Not enough no-anti-pattern functions ({len(no_ap)}) to draw {SAMPLE_SIZE}"
    )

# Step 4: random sample of 385
sample = no_ap.sample(n=SAMPLE_SIZE, random_state=RANDOM_SEED)

sample[["project", "file", "function", "func_body"]].to_csv(OUTPUT_CSV, index=False)
print(f"Saved {SAMPLE_SIZE} rows to {OUTPUT_CSV}")
