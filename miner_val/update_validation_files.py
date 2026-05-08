"""
Removes the 53 'Unhandled Exception' rows from both validation files and
appends the 53 manually validated replacement rows.
"""

import pandas as pd

ERIC_CSV      = "miner_val/tool_validation_eric.csv"
JAIRO_CSV     = "miner_val/tool_validation_jairo.csv"
VALIDATED_CSV = "miner_val/ap_replacement_sample_validated.csv"

new_rows = pd.read_csv(VALIDATED_CSV)
new_rows = new_rows[["project", "file", "function", "func_body",
                     "anti_pattern", "confidence_level", "has_ap"]]

for path in [ERIC_CSV, JAIRO_CSV]:
    df = pd.read_csv(path)
    before = len(df)
    df = df[df["anti_pattern"] != "Unhandled Exception"].copy()
    removed = before - len(df)

    df = df[["project", "file", "function", "func_body",
             "anti_pattern", "confidence_level", "has_ap"]]

    df = pd.concat([df, new_rows], ignore_index=True)
    df.index.name = "Unnamed: 0"
    df.reset_index(inplace=True)

    df.to_csv(path, index=False)
    print(f"{path}: removed {removed} UE rows, added {len(new_rows)}, "
          f"total={len(df)}")
    print(f"  anti_pattern counts:")
    print(df["anti_pattern"].value_counts().to_string())
    print()
