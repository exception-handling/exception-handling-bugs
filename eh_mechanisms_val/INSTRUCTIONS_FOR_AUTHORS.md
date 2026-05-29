# Validation Instructions — EH Mechanisms Extraction

You have **two tasks** to complete, each with its own CSV file.  
Work **independently** — do not share your answers with the other author until
both of you are done with both parts.

---

## Part A — Positive Sample (mechanism was detected)

### File: `eh_mechanisms_sample_authorX.csv`  (384 rows)

Each row is a mechanism the miner claimed to detect.  
Your job: **confirm the extracted snippet matches the claimed type**.

### Columns to read

| Column | What it contains |
|---|---|
| `mechanism_type` | The type the miner claimed to have detected |
| `mechanism_snippet` | The actual code snippet extracted by the miner |
| `func_body` | The full function body — use for context if the snippet is unclear |

### Decision criteria — `is_correct`

| Mechanism type | Mark **Y** if… | Mark **N** if… |
|---|---|---|
| `try-except` | The snippet contains a `try` block with at least one `except` clause | No `except` clause is present |
| `raise` | The snippet is a `raise` statement (with or without an argument) | It is not a raise statement |
| `try-finally` | The snippet contains a `try` block with a `finally` clause | No `finally` clause is present |
| `try-else` | The snippet contains a `try` block with both an `except` **and** an `else` clause | Either clause is missing |

> You are **not** judging code quality, style, or best practices.  
> Only check whether the snippet matches the claimed `mechanism_type`.

### How to fill in Part A

- Write `Y` or `N` in `is_correct`.
- `notes` is optional for `Y` rows.
- For `N` rows, **always** add a brief explanation  
  (e.g. *"snippet is a try-finally, not try-except"*).

---

## Part B — Negative Sample (miner detected nothing)

### File: `eh_negative_sample_authorX.csv`  (384 rows)

Each row is a function where the miner found **no** exception handling
mechanism.  There is no snippet — the miner predicted "nothing here".  
Your job: **check whether the function actually contains any EH mechanism
that the miner missed**.

### Columns to read

| Column | What it contains |
|---|---|
| `func_body` | The full function body to inspect |

### Decision criteria — `has_mechanism`

Read `func_body` carefully and look for any of the four constructs:

| Construct | What to look for |
|---|---|
| `try-except` | A `try:` block with at least one `except` clause |
| `raise` | A `raise` statement anywhere in the function |
| `try-finally` | A `try:` block with a `finally:` clause |
| `try-else` | A `try:` block with both an `except` and an `else:` clause |

- **`has_mechanism = N`** — no EH construct found → miner was correct (True Negative)
- **`has_mechanism = Y`** — you spotted a construct the miner missed → False Negative

### How to fill in Part B

- Write `Y` or `N` in `has_mechanism`.
- If `Y`: fill in `mechanism_found` with the type(s) you spotted  
  (e.g. `raise`, or `try-except, raise` if you found more than one).
- `notes` is optional but helpful when marking `Y`.

---

## After both authors are done

1. Share your completed files with each other.
2. Compute inter-rater agreement (Cohen's Kappa) separately for Part A and Part B
   — use `experiment_val/agreement.py` as a reference.
3. For every row where your answers differ, **discuss until you reach consensus**.
4. Record the consensus in both author files, then run:
   ```bash
   python3 eh_mechanisms_val/compute_precision.py
   ```
   to get precision, recall, F1, and accuracy.

---

## Frequently asked questions

**The snippet is cut off — can I still judge it? (Part A)**  
Use `func_body` to find the full construct. If even the function body is
unclear, mark `N` and note *"snippet truncated, cannot confirm"*.

**The `try` block has both `except` and `finally` — which type is it? (Part A)**  
A single `try` block can be two mechanisms. Trust only the `mechanism_type`
column. If the claimed type is `try-except` and the snippet has an `except`
clause (even if it also has a `finally`), mark `Y`.

**The `raise` is inside an `except` block — does it count? (Parts A & B)**  
Yes. A `raise` is a valid mechanism regardless of where it appears in the
function.

**The function is a test or stub — does that matter? (Parts A & B)**  
No. Validation is about extraction correctness, not code quality. If the
construct is present, mark `Y`.

**The function body is very short or empty — Part B**  
If the function body contains only `pass`, a docstring, or a single expression
with no EH construct, mark `has_mechanism = N`.
