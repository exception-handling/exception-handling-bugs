# EH Mechanisms Extraction Validation Plan

## Goal

Measure **precision, recall, F1, and accuracy** of the mechanism extraction step
in the Exception Miner tool, in support of the following paper statement
(reviewer R1Q5):

> "To evaluate whether the extracted exception handling mechanisms were affected
> by false positives, we manually validated a stratified sample of 384 mechanisms
> (95% confidence level, 5% margin of error).  The extraction step achieved
> XX% precision, with detailed results by mechanism type available in the
> supplementary material."

---

## Background

The miner extracts four mechanism types directly from Python AST node types:

| Mechanism | AST node | Miner column |
|---|---|---|
| `try-except` | `try_statement` with ≥1 except handler | `n_try_except` |
| `raise` | `raise_statement` | `n_raise` |
| `try-finally` | `try_statement` with a finally clause | `n_finally` |
| `try-else` | `try_statement` with handlers **and** an else clause | `n_try_else` |

Because these correspond to unambiguous AST constructs, the main risk is a
**false positive**: the miner counts a mechanism that is not actually present
(e.g., due to a parser bug or encoding issue).  A **negative sample** is also
validated to detect any false negatives (mechanisms the miner silently missed).

---

## Two-set Design

| Set | File(s) | Size | Purpose |
|---|---|---|---|
| Positive | `eh_mechanisms_sample_author1/2.csv` | 384 rows | Functions where miner detected ≥1 mechanism → verify each snippet is correct |
| Negative | `eh_negative_sample_author1/2.csv` | 384 rows | Functions where miner detected nothing → check if any mechanism was missed |

**Total evaluated: 768 rows** across two independently worked author copies.

### Confusion matrix

| | Mechanism present | No mechanism |
|---|---|---|
| **Miner detected** | TP (`is_correct=Y` in positive set) | FP (`is_correct=N` in positive set) |
| **Miner missed** | FN (`has_mechanism=Y` in negative set) | TN (`has_mechanism=N` in negative set) |

```
Precision = TP / (TP + FP)
Recall    = TP / (TP + FN)
F1        = 2 · Precision · Recall / (Precision + Recall)
Accuracy  = (TP + TN) / (TP + FP + TN + FN)
```

---

## Positive Sample Design

Stratified proportional allocation, n = 384 (95% CI, 5% margin of error).
Allocation computed with the largest-remainder method on total instance counts
from the full miner output (`dataset/final_dataset/`):

| Mechanism | Instances in dataset | % | Allocated |
|---|---|---|---|
| `try-except` | 78,193 | 33.15% | 127 |
| `raise` | 145,035 | 61.48% | 236 |
| `try-finally` | 8,170 | 3.46% | 13 |
| `try-else` | 4,511 | 1.91% | 8 |
| **TOTAL** | **235,909** | **100%** | **384** |

Within each stratum, rows are drawn uniformly at random (without replacement)
from the pool of functions where the corresponding count column is > 0.
For each sampled function, one representative snippet is extracted from
`func_body` using Python's `ast` module and shown in `mechanism_snippet`.

## Negative Sample Design

Uniform random sample, n = 384, drawn from the pool of functions where
**all four** mechanism count columns equal 0:

| | Count |
|---|---|
| Total functions in `dataset/final_dataset/` | 1,295,543 |
| Functions with ≥1 detected mechanism (positive pool) | 140,360 |
| Functions with no detected mechanism (negative pool) | **1,155,183** |
| Negative sample size | **384** |

No mechanism_snippet is provided — validators read the full `func_body`.

---

## Files

| File | Description |
|---|---|
| `build_eh_mechanisms_sample.py` | Generates the positive sample CSVs |
| `build_eh_negative_sample.py` | Generates the negative sample CSVs |
| `compute_precision.py` | Computes metrics after validation is complete |
| `eh_mechanisms_sample_author1.csv` | Positive validation sheet — Author 1 |
| `eh_mechanisms_sample_author2.csv` | Positive validation sheet — Author 2 |
| `eh_negative_sample_author1.csv` | Negative validation sheet — Author 1 |
| `eh_negative_sample_author2.csv` | Negative validation sheet — Author 2 |
| `INSTRUCTIONS_FOR_AUTHORS.md` | Step-by-step protocol for validators |

---

## Validation CSV Columns

### Positive sample (`is_correct` to fill)

| Column | Description |
|---|---|
| `id` | Row identifier (1–384) |
| `project` | GitHub project name |
| `file` | Project-relative file path |
| `function` | Function name |
| `mechanism_type` | Claimed mechanism: `try-except`, `raise`, `try-finally`, `try-else` |
| `mechanism_snippet` | Extracted code of one instance of the mechanism |
| `func_body` | Full function body (surrounding context) |
| `is_correct` | **To fill:** `Y` if snippet matches claimed type, `N` otherwise |
| `notes` | **To fill:** required for `N` rows |

### Negative sample (`has_mechanism` to fill)

| Column | Description |
|---|---|
| `id` | Row identifier (1–384) |
| `project` | GitHub project name |
| `file` | Project-relative file path |
| `function` | Function name |
| `func_body` | Full function body to inspect for any missed mechanism |
| `has_mechanism` | **To fill:** `N` = no mechanism found (TN), `Y` = mechanism spotted (FN) |
| `mechanism_found` | **To fill:** if `Y`, which type(s) were found |
| `notes` | **To fill:** optional comment |

---

## Inter-rater Agreement

After both authors complete their sheets independently, compute Cohen's Kappa
(and percent agreement) for each set:
- Positive set: compare `is_correct` column between author 1 and author 2
- Negative set: compare `has_mechanism` column between author 1 and author 2

Use `experiment_val/agreement.py` as a reference implementation.

---

## How to Reproduce

```bash
# From the repository root

# Step 1: build positive sample (384 rows, stratified by mechanism type)
python3 eh_mechanisms_val/build_eh_mechanisms_sample.py

# Step 2: build negative sample (384 rows, uniform random from no-mechanism pool)
python3 eh_mechanisms_val/build_eh_negative_sample.py

# Step 3: (manual) both authors independently fill their CSV files

# Step 4: compute final metrics
python3 eh_mechanisms_val/compute_precision.py
```

All random operations use seed 42 for full reproducibility.
