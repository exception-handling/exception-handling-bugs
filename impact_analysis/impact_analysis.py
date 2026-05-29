"""
Impact analysis of Python exception handling bugs.

Maps observed symptoms from the main dataset to 7 impact categories,
computes their distribution, identifies top root causes per category,
and selects real-world examples from distinct projects.

Output: impact_analysis_with_examples.csv (same directory)
"""

import pandas as pd
from pathlib import Path

HERE = Path(__file__).parent
BUGS_CSV = HERE.parent / "dataset" / "bugs" / "dataset_exception_bugs.csv"
OUT_CSV = HERE / "impact_analysis_with_examples.csv"

# ---------------------------------------------------------------------------
# Symptom → impact category mapping
# ---------------------------------------------------------------------------
IMPACT_MAP = {
    "Unexpected Application Crash"                              : "Crash or Abrupt Termination",
    "System Freeze or Deadlock"                                 : "Crash or Abrupt Termination",
    "Compilation or Syntax Error"                               : "Crash or Abrupt Termination",
    "Modules/App Init"                                          : "Crash or Abrupt Termination",
    "Failure to Handle Expected Exceptions"                     : "Incorrect Behavior",
    "Incorrect Error Recovery"                                  : "Incorrect Behavior",
    "Unexpected Control Flow"                                   : "Incorrect Behavior",
    "UI Malfunction or Rendering Issues"                        : "Incorrect Behavior",
    "Database Query Failure or Data Inconsistency"              : "Incorrect Behavior",
    "Inconsistency Between Modules"                             : "Incorrect Behavior",
    "Incorrect or Misleading Error Message"                     : "Misleading Diagnostics",
    "Poor Debugging"                                            : "Misleading Diagnostics",
    "Failure Due to External API Change or Misuse"              : "Compatibility Failure",
    "Compatibility Errors Due to Python Version or Dependencies": "Compatibility Failure",
    "Import Error"                                              : "Compatibility Failure",
    "Partial Functionality"                                     : "Silent Failure",
    "Performance Degradation Due to Exception Handling"         : "Performance Degradation",
    "Failure in Continuous Integration (CI) Pipeline"           : "CI/Build Disruption",
}

CATEGORIES = [
    "Incorrect Behavior",
    "Crash or Abrupt Termination",
    "Misleading Diagnostics",
    "Silent Failure",
    "CI/Build Disruption",
    "Performance Degradation",
    "Compatibility Failure",
]

DESCRIPTIONS = {
    "Incorrect Behavior"          : (
        "Program continues execution but produces wrong outcomes: failed exception "
        "recovery, unexpected control flow, or data inconsistency"
    ),
    "Crash or Abrupt Termination" : (
        "Program execution is interrupted unexpectedly due to an unhandled or "
        "improperly propagated exception, causing a crash or deadlock"
    ),
    "Misleading Diagnostics"      : (
        "Error messages are inaccurate, incomplete, or obscure the actual failure, "
        "hindering debugging and root-cause identification"
    ),
    "Silent Failure"              : (
        "Exception is suppressed or handled too broadly, hiding the underlying "
        "problem and causing the program to appear functional while delivering "
        "partial or incorrect results"
    ),
    "CI/Build Disruption"         : (
        "Exception handling defects cause build or test suite failures, blocking "
        "continuous integration pipelines and developer workflows"
    ),
    "Performance Degradation"     : (
        "Improper exception handling introduces unnecessary overhead (e.g., catching "
        "and re-raising in hot paths), causing measurable slowdowns"
    ),
    "Compatibility Failure"       : (
        "Exception handling code breaks across API versions, library updates, or "
        "Python versions due to misuse of exception APIs or import errors"
    ),
}

RELATED_SYMPTOMS = {
    "Incorrect Behavior"          : (
        "Failure to Handle Expected Exceptions; Incorrect Error Recovery; "
        "Unexpected Control Flow; UI Malfunction; Database Failure"
    ),
    "Crash or Abrupt Termination" : (
        "Unexpected Application Crash; System Freeze or Deadlock; "
        "Compilation/Syntax Error; App Init Failure"
    ),
    "Misleading Diagnostics"      : "Incorrect or Misleading Error Message; Poor Debugging Experience",
    "Silent Failure"              : "Partial Functionality",
    "CI/Build Disruption"         : "Failure in Continuous Integration (CI) Pipeline",
    "Performance Degradation"     : "Performance Degradation Due to Exception Handling",
    "Compatibility Failure"       : (
        "Failure Due to External API Change or Misuse; "
        "Python Version Compatibility Errors; Import Errors"
    ),
}


def load_bugs() -> pd.DataFrame:
    df = pd.read_csv(BUGS_CSV)
    df = df[df["exception_bug"] == "Y"].copy()
    df["symptom_grp"] = df["symptom_grp"].str.strip()
    df["root_cause_map"] = df["root_cause_map"].str.strip()
    df["impact_category"] = df["symptom_grp"].map(IMPACT_MAP)
    return df


def top_root_causes(sub: pd.DataFrame, n: int = 3) -> str:
    counts = sub["root_cause_map"].value_counts().head(n)
    return "; ".join(f"{rc} ({cnt})" for rc, cnt in counts.items())


def pick_examples(df: pd.DataFrame, category: str, n: int = 2) -> list[str]:
    sub = df[
        (df["impact_category"] == category)
        & df["url_issue_x"].notna()
        & df["root_cause_map"].notna()
    ].drop_duplicates(subset=["project"])
    examples = []
    for _, row in sub.head(n).iterrows():
        examples.append(f"{row['project']} ({row['url_issue_x']})")
    while len(examples) < n:
        examples.append("")
    return examples


def build_table(df: pd.DataFrame) -> pd.DataFrame:
    total = len(df)
    rows = []
    for cat in CATEGORIES:
        sub = df[df["impact_category"] == cat].dropna(subset=["root_cause_map"])
        n = len(df[df["impact_category"] == cat])
        examples = pick_examples(df, cat)
        rows.append({
            "Impact Category"        : cat,
            "Description"            : DESCRIPTIONS[cat],
            "n"                      : n,
            "Percentage (%)"         : round(100 * n / total, 1),
            "Related Symptoms"       : RELATED_SYMPTOMS[cat],
            "Top Root Causes (count)": top_root_causes(sub),
            "Real-world Example 1"   : examples[0],
            "Real-world Example 2"   : examples[1],
        })
    return pd.DataFrame(rows)


def main() -> None:
    df = load_bugs()
    print(f"Confirmed exception bugs: {len(df)}")

    table = build_table(df)
    table.to_csv(OUT_CSV, index=False)
    print(f"Saved: {OUT_CSV}")
    print()
    print(table[["Impact Category", "n", "Percentage (%)", "Top Root Causes (count)"]].to_string(index=False))


if __name__ == "__main__":
    main()
