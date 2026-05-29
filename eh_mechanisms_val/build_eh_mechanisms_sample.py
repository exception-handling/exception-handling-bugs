"""
Builds a stratified sample of 384 exception handling mechanisms to validate
the precision of the extraction step (false-positive rate).

Context
-------
The miner extracts four mechanism types from Python AST nodes:
  - try-except   → Try nodes with at least one except handler
  - raise        → Raise statement nodes
  - try-finally  → Try nodes with a finally clause
  - try-else     → Try nodes with both an except handler AND an else clause

Two authors will independently inspect each sampled mechanism and its
surrounding function context to confirm the extracted snippet matches the
claimed mechanism type.  Disagreements are resolved by discussion.

Sample design
-------------
Stratified proportional allocation, n = 384 (95% confidence, 5% margin of
error), using largest-remainder rounding:

  Mechanism     Instances in full dataset   Allocated
  -----------   -------------------------   ---------
  try-except                       78,193         127
  raise                           145,035         236
  try-finally                       8,170          13
  try-else                          4,511           8
  -----------   -------------------------   ---------
  TOTAL                           235,909         384

Within each stratum the pool is all (project, file, function) rows from
dataset/final_dataset/ where the mechanism count column is > 0.  One row is
drawn per function (uniform random, without replacement).  If the ast parser
can extract an individual snippet from the function body, it is included as
mechanism_snippet; otherwise the column is left blank and the full func_body
serves as the validation context.

Outputs
-------
  eh_mechanisms_val/eh_mechanisms_sample_author1.csv
  eh_mechanisms_val/eh_mechanisms_sample_author2.csv

Both files are identical; each author fills in is_correct (Y/N) and notes
independently, then disagreements are resolved through discussion.
"""

import ast
import glob
import os
import random
import sys

import pandas as pd

# ── configuration ─────────────────────────────────────────────────────────────
FINAL_DATASET_DIR = "dataset/final_dataset"
OUT_AUTHOR1       = "eh_mechanisms_val/eh_mechanisms_sample_author1.csv"
OUT_AUTHOR2       = "eh_mechanisms_val/eh_mechanisms_sample_author2.csv"
RANDOM_SEED       = 42
TOTAL_SAMPLE      = 384

# Allocation (largest-remainder method, proportional to total instance counts)
ALLOCATION: dict[str, int] = {
    "try-except":  127,
    "raise":       236,
    "try-finally":  13,
    "try-else":      8,
}

# Miner column that counts instances of each mechanism per function
MECH_COL: dict[str, str] = {
    "try-except":  "n_try_except",
    "raise":       "n_raise",
    "try-finally": "n_finally",
    "try-else":    "n_try_else",
}

assert sum(ALLOCATION.values()) == TOTAL_SAMPLE, "Allocation must sum to TOTAL_SAMPLE"


# ── snippet extraction ────────────────────────────────────────────────────────

def extract_snippet(func_body: str, mechanism_type: str, rng: random.Random) -> str:
    """
    Parse *func_body* with ast and return one representative code snippet for
    the given *mechanism_type*.  Returns an empty string if parsing fails or
    no matching node is found.
    """
    try:
        tree = ast.parse(func_body)
    except SyntaxError:
        return ""

    snippets: list[str] = []

    class _Visitor(ast.NodeVisitor):
        def visit_Try(self, node: ast.Try) -> None:
            text = ast.get_source_segment(func_body, node) or ""
            has_handlers = bool(node.handlers)
            has_finally  = bool(node.finalbody)
            has_else     = bool(node.orelse)

            if mechanism_type == "try-except" and has_handlers:
                snippets.append(text)
            if mechanism_type == "try-finally" and has_finally:
                snippets.append(text)
            if mechanism_type == "try-else" and has_handlers and has_else:
                snippets.append(text)

            self.generic_visit(node)

        # Python 3.11+ introduces TryStar (except*); handle gracefully
        def visit_TryStar(self, node: ast.AST) -> None:  # type: ignore[name-defined]
            if mechanism_type == "try-except":
                text = ast.get_source_segment(func_body, node) or ""  # type: ignore[arg-type]
                if text:
                    snippets.append(text)
            self.generic_visit(node)

        def visit_Raise(self, node: ast.Raise) -> None:
            if mechanism_type == "raise":
                text = ast.get_source_segment(func_body, node) or ""
                snippets.append(text)
            self.generic_visit(node)

    _Visitor().visit(tree)
    return rng.choice(snippets) if snippets else ""


def shorten_path(path: str) -> str:
    """
    Strip the machine-specific prefix up to the project root, keeping only the
    path from the project name onward (e.g. 'starlette/tests/test_foo.py').
    """
    # Normalise: find the 'projects/py/<project>/' segment
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


# ── stratified sampling ───────────────────────────────────────────────────────

def build_sample(combined: pd.DataFrame, rng: random.Random) -> pd.DataFrame:
    parts: list[pd.DataFrame] = []

    for mtype, n_alloc in ALLOCATION.items():
        col = MECH_COL[mtype]
        pool = combined[combined[col] > 0].copy()
        print(f"  {mtype:12s}: pool = {len(pool):>7,}, allocating {n_alloc}")

        if len(pool) < n_alloc:
            sys.exit(
                f"ERROR: not enough candidates for '{mtype}': "
                f"need {n_alloc}, have {len(pool)}"
            )

        drawn = pool.sample(n=n_alloc, random_state=rng.randint(0, 2**31))
        drawn = drawn[["project", "file", "function", "func_body"]].copy()
        drawn["mechanism_type"] = mtype
        parts.append(drawn)

    sample = pd.concat(parts, ignore_index=True)

    # Shuffle rows so both mechanism types are interleaved (harder to spot
    # patterns) — use a fixed seed for reproducibility
    sample = sample.sample(frac=1, random_state=RANDOM_SEED).reset_index(drop=True)
    sample.index = sample.index + 1          # 1-based id
    sample.index.name = "id"
    return sample


# ── extract snippets (one per row) ───────────────────────────────────────────

def add_snippets(sample: pd.DataFrame, rng: random.Random) -> pd.DataFrame:
    snippets: list[str] = []
    failed = 0
    for _, row in sample.iterrows():
        snip = extract_snippet(
            str(row["func_body"]),
            str(row["mechanism_type"]),
            rng,
        )
        snippets.append(snip)
        if not snip:
            failed += 1

    sample = sample.copy()
    sample["mechanism_snippet"] = snippets

    # Shorten absolute file paths for readability
    sample["file"] = sample["file"].apply(shorten_path)

    if failed:
        print(
            f"  Warning: snippet extraction failed for {failed} rows "
            f"(func_body will serve as context)"
        )
    return sample


# ── build final output columns ────────────────────────────────────────────────

def format_output(sample: pd.DataFrame) -> pd.DataFrame:
    """
    Return the DataFrame in the column order expected by the validators,
    with blank columns for their responses.
    """
    return sample[[
        "project",
        "file",
        "function",
        "mechanism_type",
        "mechanism_snippet",
        "func_body",
        "is_correct",    # blank — validator fills Y / N
        "notes",         # blank — validator fills free-form notes
    ]]


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    rng = random.Random(RANDOM_SEED)

    print("Loading dataset …")
    combined = load_dataset()

    print("\nInstance counts by mechanism type:")
    grand_total = 0
    for mtype, col in MECH_COL.items():
        total = int(combined[col].sum())
        grand_total += total
        print(f"  {mtype:12s}: {total:>8,}")
    print(f"  {'TOTAL':12s}: {grand_total:>8,}")

    print("\nSampling …")
    sample = build_sample(combined, rng)

    print("\nExtracting mechanism snippets …")
    sample = add_snippets(sample, rng)

    # Add blank validator columns
    sample["is_correct"] = ""
    sample["notes"] = ""

    output = format_output(sample)
    output = output.reset_index()  # bring 'id' back as column

    print(f"\nFinal sample: {len(output)} rows")
    print("Mechanism type distribution:")
    print(output["mechanism_type"].value_counts().to_string())

    os.makedirs("eh_mechanisms_val", exist_ok=True)
    output.to_csv(OUT_AUTHOR1, index=False)
    output.to_csv(OUT_AUTHOR2, index=False)
    print(f"\nSaved:\n  {OUT_AUTHOR1}\n  {OUT_AUTHOR2}")
    print(
        "\nEach author should fill in 'is_correct' (Y/N) and 'notes' "
        "independently, then disagreements are resolved by discussion."
    )


if __name__ == "__main__":
    main()
