"""
For every commit, identifies which functions were CHANGED by the fix
using a strict line-level diff (difflib) on function bodies.

A function is included only when at least one added or removed line is
EXECUTABLE — meaning it is non-blank and not a pure comment (#...).
This avoids false positives from whitespace reformatting or comment edits.

Requires fixes_val/miner_before.csv and fixes_val/miner_after.csv
(run 02_mine_commits.py first).

Output:
  fixes_val/miner_diff.csv
    project, commit_fix, file, function,
    func_body_before, func_body_after, change_type,
    <AP_col>_before, <AP_col>_after  (one row per changed function)
"""

import difflib
import pandas as pd

BEFORE_CSV = "fixes_val/miner_before.csv"
AFTER_CSV  = "fixes_val/miner_after.csv"
OUT_CSV    = "fixes_val/miner_diff.csv"

AP_COLS = [
    "n_bare_except", "n_generic_except", "n_captures_broad_raise",
    "n_try_pass", "n_bare_raise_finally",
    "n_captures_misplaced_bare_raise", "n_nested_try",
]


def has_executable_changes(body_before, body_after) -> bool:
    """
    True if at least one added or removed line between the two bodies
    is executable (non-blank, not a pure # comment).
    """
    before_lines = str(body_before).splitlines() if pd.notna(body_before) else []
    after_lines  = str(body_after).splitlines()  if pd.notna(body_after)  else []

    for line in difflib.unified_diff(before_lines, after_lines, lineterm=""):
        if line.startswith(("+", "-")) and not line.startswith(("+++", "---")):
            content = line[1:].strip()
            if content and not content.startswith("#"):
                return True
    return False


before = pd.read_csv(BEFORE_CSV)
after  = pd.read_csv(AFTER_CSV)

KEY = ["project", "commit_fix", "file", "function"]

merged = pd.merge(
    before[KEY + ["func_body"] + AP_COLS].rename(
        columns={c: f"{c}_before" for c in AP_COLS + ["func_body"]}),
    after[KEY + ["func_body"] + AP_COLS].rename(
        columns={c: f"{c}_after" for c in AP_COLS + ["func_body"]}),
    on=KEY, how="outer"
)


def change_type(row):
    has_before = pd.notna(row.get("func_body_before"))
    has_after  = pd.notna(row.get("func_body_after"))
    if has_before and has_after:
        return "modified"
    elif has_after:
        return "added"
    return "removed"

merged["change_type"] = merged.apply(change_type, axis=1)

# Added/removed functions are always included (whole body is the change).
# Modified functions only if they have at least one executable line diff.
added_removed = merged[merged["change_type"].isin(["added", "removed"])]

modified = merged[merged["change_type"] == "modified"].copy()
modified["has_exec_change"] = modified.apply(
    lambda r: has_executable_changes(r["func_body_before"], r["func_body_after"]),
    axis=1,
)
modified_strict = modified[modified["has_exec_change"]].drop(columns="has_exec_change")

diff = pd.concat([added_removed, modified_strict], ignore_index=True)
diff.to_csv(OUT_CSV, index=False)

print(f"Changed functions (strict): {len(diff)}")
print(diff["change_type"].value_counts().to_string())
print(f"\nSaved to {OUT_CSV}")
