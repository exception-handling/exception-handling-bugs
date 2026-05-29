"""
Produces an AP-level summary table from delta_table.csv by summing
before/after/delta columns across all projects and fix commits.

Output matches the numbers cited in the manuscript:
  total before = 5,844  |  total after = 6,040  |  net = +196

Usage
-----
  python3 fixes_val/05_summarize_delta.py
"""

import pandas as pd

INPUT  = "fixes_val/delta_table.csv"
OUTPUT = "fixes_val/ap_summary.csv"

AP_META = [
    ("Too Broad Except",           "n_generic_except"),
    ("Swallowing Exceptions",      "n_try_pass"),
    ("Too Broad Raising",          "n_captures_broad_raise"),
    ("Bare Except Catch Block",    "n_bare_except"),
    ("Nested Try-Except Blocks",   "n_nested_try"),
    ("Bare Raise Block",           "n_captures_misplaced_bare_raise"),
    ("Bare Raise inside Finally",  "n_bare_raise_finally"),
]

delta = pd.read_csv(INPUT)

rows = []
for label, col in AP_META:
    total_before = delta[f"{col}_before"].sum()
    total_after  = delta[f"{col}_after"].sum()
    net          = delta[f"{col}_delta"].sum()
    pct          = (net / total_before * 100) if total_before else 0.0
    rows.append({
        "anti_pattern": label,
        "column":       col,
        "total_before": int(total_before),
        "total_after":  int(total_after),
        "delta":        int(net),
        "pct_change":   round(pct, 2),
    })

summary = pd.DataFrame(rows)

# Total row
grand_before = summary["total_before"].sum()
grand_after  = summary["total_after"].sum()
grand_delta  = summary["delta"].sum()
total_row = pd.DataFrame([{
    "anti_pattern": "TOTAL",
    "column":       "",
    "total_before": grand_before,
    "total_after":  grand_after,
    "delta":        grand_delta,
    "pct_change":   round(grand_delta / grand_before * 100, 2),
}])

summary = pd.concat([summary, total_row], ignore_index=True)

summary.to_csv(OUTPUT, index=False)

print(summary.to_string(index=False))
print(f"\nSaved to {OUTPUT}")
