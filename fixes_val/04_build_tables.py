"""
Builds three summary tables from the mined data:

1. delta_table.csv      — per-commit, per-AP-type: before / after / delta counts
2. ap_summary.csv       — aggregate AP counts before vs after across all commits
3. diff_ap_report.csv   — APs introduced / removed / net in the diff functions

Requires: miner_before.csv, miner_after.csv, miner_diff.csv
"""

import pandas as pd

BEFORE_CSV  = "fixes_val/miner_before.csv"
AFTER_CSV   = "fixes_val/miner_after.csv"
DIFF_CSV    = "fixes_val/miner_diff.csv"
DELTA_OUT   = "fixes_val/delta_table.csv"
SUMMARY_OUT = "fixes_val/ap_summary.csv"
DIFF_OUT    = "fixes_val/diff_ap_report.csv"

AP_COLS = [
    "n_bare_except", "n_generic_except", "n_captures_broad_raise",
    "n_try_pass", "n_bare_raise_finally",
    "n_captures_misplaced_bare_raise", "n_nested_try",
]

AP_LABELS = {
    "n_bare_except":                   "Bare Except Catch Block",
    "n_generic_except":                "Too Broad Except",
    "n_captures_broad_raise":          "Too Broad Raising",
    "n_try_pass":                      "Swallowing Exceptions",
    "n_bare_raise_finally":            "Bare Raise inside Finally",
    "n_captures_misplaced_bare_raise": "Bare Raise Block",
    "n_nested_try":                    "Nested Try-Except Blocks",
}

before = pd.read_csv(BEFORE_CSV)
after  = pd.read_csv(AFTER_CSV)
diff   = pd.read_csv(DIFF_CSV)

KEY = ["project", "commit_fix", "file", "function"]

# ── Table 1: per-commit delta ─────────────────────────────────────────────────
before_sum = before.groupby(["project", "commit_fix"])[AP_COLS].sum().reset_index()
after_sum  = after.groupby(["project", "commit_fix"])[AP_COLS].sum().reset_index()

delta = pd.merge(
    before_sum.rename(columns={c: f"{c}_before" for c in AP_COLS}),
    after_sum.rename( columns={c: f"{c}_after"  for c in AP_COLS}),
    on=["project", "commit_fix"], how="outer"
).fillna(0)

for c in AP_COLS:
    delta[f"{c}_delta"] = delta[f"{c}_after"] - delta[f"{c}_before"]

delta.to_csv(DELTA_OUT, index=False)
print(f"Delta table: {len(delta)} rows → {DELTA_OUT}")

# ── Table 2: aggregate AP summary ────────────────────────────────────────────
rows = []
for col in AP_COLS:
    b = int(before[col].sum())
    a = int(after[col].sum())
    rows.append({
        "anti_pattern":  AP_LABELS[col],
        "column":        col,
        "total_before":  b,
        "total_after":   a,
        "delta":         a - b,
        "pct_change":    round((a - b) / b * 100, 2) if b else None,
    })

summary = pd.DataFrame(rows).sort_values("total_before", ascending=False)
summary.to_csv(SUMMARY_OUT, index=False)
print(f"\nAggregate AP summary:\n{summary.to_string(index=False)}")
print(f"\n→ {SUMMARY_OUT}")

# ── Table 3: diff AP report ───────────────────────────────────────────────────
diff_rows = []
for col in AP_COLS:
    b_col = f"{col}_before"
    a_col = f"{col}_after"
    b = diff[b_col].fillna(0)
    a = diff[a_col].fillna(0)
    introduced = int(((a > 0) & (b == 0)).sum())
    removed    = int(((b > 0) & (a == 0)).sum())
    increased  = int(((a > b) & (b > 0)).sum())
    decreased  = int(((b > a) & (a > 0)).sum())
    unchanged  = int(((a == b) & (a > 0)).sum())
    diff_rows.append({
        "anti_pattern": AP_LABELS[col],
        "column":       col,
        "introduced":   introduced,  # 0→>0
        "removed":      removed,     # >0→0
        "increased":    increased,   # >0→more
        "decreased":    decreased,   # >0→less
        "unchanged":    unchanged,   # >0 in both, same count
        "net":          introduced - removed,
    })

diff_report = pd.DataFrame(diff_rows)
diff_report.to_csv(DIFF_OUT, index=False)
print(f"\nDiff AP report:\n{diff_report.to_string(index=False)}")
print(f"\n→ {DIFF_OUT}")
