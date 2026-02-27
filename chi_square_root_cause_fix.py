#!/usr/bin/env python3
"""Chi-square and Cramer's V analysis for root-cause vs fix co-occurrence matrix."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import List, Tuple

import numpy as np
from scipy.stats import chi2_contingency


def load_contingency_matrix(csv_path: Path) -> Tuple[List[str], List[str], np.ndarray]:
    """Load a contingency matrix from CSV where first column is row labels."""
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        if len(header) < 2:
            raise ValueError("CSV must contain one label column and at least one numeric column.")

        col_labels = [c.strip() for c in header[1:]]
        row_labels: List[str] = []
        matrix_rows: List[List[float]] = []

        for row in reader:
            if not row:
                continue
            row_labels.append(row[0].strip())
            values = [float(cell) if cell.strip() else 0.0 for cell in row[1:]]
            if len(values) != len(col_labels):
                raise ValueError(
                    f"Row '{row[0]}' has {len(values)} values, expected {len(col_labels)}."
                )
            matrix_rows.append(values)

    matrix = np.array(matrix_rows, dtype=float)
    if matrix.size == 0:
        raise ValueError("CSV has no data rows.")
    return row_labels, col_labels, matrix


def cramers_v(chi2: float, n: float, r: int, c: int, bias_correction: bool = False) -> float:
    """Compute Cramer's V (optionally bias-corrected)."""
    if n <= 0:
        return float("nan")

    phi2 = chi2 / n

    if not bias_correction:
        denom = min(r - 1, c - 1)
        return np.sqrt(phi2 / denom) if denom > 0 else float("nan")

    if n <= 1:
        return float("nan")

    phi2corr = max(0.0, phi2 - ((c - 1) * (r - 1)) / (n - 1))
    rcorr = r - ((r - 1) ** 2) / (n - 1)
    ccorr = c - ((c - 1) ** 2) / (n - 1)
    denom = min(rcorr - 1, ccorr - 1)

    return np.sqrt(phi2corr / denom) if denom > 0 else 0.0


def effect_size_label(v: float) -> str:
    """Interpret Cramer's V with common thresholds."""
    if np.isnan(v):
        return "undefined"
    if v < 0.10:
        return "negligible"
    if v < 0.30:
        return "small"
    if v < 0.50:
        return "medium"
    return "large"


def chi2_statistic_from_table(table: np.ndarray) -> float:
    """Compute chi-square statistic robustly, ignoring zero-expected cells."""
    row_sums = table.sum(axis=1, keepdims=True)
    col_sums = table.sum(axis=0, keepdims=True)
    total = table.sum()

    if total <= 0:
        return float("nan")

    expected = (row_sums @ col_sums) / total
    with np.errstate(divide="ignore", invalid="ignore"):
        contributions = np.where(expected > 0, (table - expected) ** 2 / expected, 0.0)
    return float(np.nansum(contributions))


def bootstrap_cramers_v_ci(
    observed: np.ndarray,
    n_bootstrap: int = 5000,
    confidence: float = 0.95,
    seed: int = 42,
    bias_correction: bool = True,
) -> Tuple[float, float]:
    """Bootstrap CI for Cramer's V using multinomial resampling."""
    if n_bootstrap < 100:
        raise ValueError("n_bootstrap must be >= 100.")
    if confidence <= 0 or confidence >= 1:
        raise ValueError("confidence must be between 0 and 1.")

    n = int(observed.sum())
    if n <= 0:
        return float("nan"), float("nan")

    flat_counts = observed.ravel().astype(float)
    probs = flat_counts / flat_counts.sum()
    r, c = observed.shape
    rng = np.random.default_rng(seed)

    values = np.empty(n_bootstrap, dtype=float)
    for b in range(n_bootstrap):
        sampled = rng.multinomial(n, probs).reshape(r, c)
        chi2_b = chi2_statistic_from_table(sampled)
        values[b] = cramers_v(
            chi2=chi2_b,
            n=n,
            r=r,
            c=c,
            bias_correction=bias_correction,
        )

    alpha = 1 - confidence
    lower = float(np.quantile(values, alpha / 2))
    upper = float(np.quantile(values, 1 - alpha / 2))
    return lower, upper


def format_p_value(p_value: float, threshold: float = 1e-4) -> str:
    """Format p-value in readable form, including very small values."""
    if p_value < threshold:
        return f"< {threshold:.4f}"
    return f"{p_value:.6f}"


def run_analysis(
    input_csv: Path,
    relation_name: str,
    alpha: float,
    n_bootstrap: int,
    confidence: float,
    pvalue_threshold: float,
    random_seed: int,
) -> None:
    _, _, observed = load_contingency_matrix(input_csv)

    chi2, p_value, dof, expected = chi2_contingency(observed, correction=False)

    n = observed.sum()
    r, c = observed.shape
    v = cramers_v(chi2, n, r, c, bias_correction=False)
    v_corr = cramers_v(chi2, n, r, c, bias_correction=True)
    ci_low, ci_high = bootstrap_cramers_v_ci(
        observed=observed,
        n_bootstrap=n_bootstrap,
        confidence=confidence,
        seed=random_seed,
        bias_correction=True,
    )

    expected_below_5 = int((expected < 5).sum())
    expected_below_1 = int((expected < 1).sum())
    total_cells = expected.size

    significant = p_value < alpha
    relation_text = "reject H0 (association exists)" if significant else "fail to reject H0"

    print("=" * 90)
    print(f"Chi-square Test: {relation_name}")
    print("=" * 90)
    print(f"Input file: {input_csv}")
    print(f"Matrix shape: {r} rows x {c} columns")
    print(f"Total observations (N): {int(n)}")
    print("")
    print("Hypotheses")
    print(f"H0: variables in '{relation_name}' are independent.")
    print(f"H1: variables in '{relation_name}' are associated.")
    print("")
    print("Results")
    print(f"chi2 statistic: {chi2:.6f}")
    print(f"degrees of freedom: {dof}")
    print(f"p-value: {format_p_value(p_value, threshold=pvalue_threshold)}")
    print(f"p-value (scientific): {p_value:.8g}")
    print(f"alpha: {alpha}")
    print(f"Decision: {relation_text}")
    print("")
    print("Effect Size")
    print(f"Cramer's V: {v:.6f} ({effect_size_label(v)})")
    print(f"Cramer's V (bias-corrected): {v_corr:.6f} ({effect_size_label(v_corr)})")
    print(f"{int(confidence*100)}% CI for Cramer's V (bias-corrected, bootstrap): [{ci_low:.6f}, {ci_high:.6f}]")
    print("")
    print("Assumption Check (expected frequencies)")
    print(f"Cells with expected < 5: {expected_below_5}/{total_cells} ({100*expected_below_5/total_cells:.2f}%)")
    print(f"Cells with expected < 1: {expected_below_1}/{total_cells} ({100*expected_below_1/total_cells:.2f}%)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run chi-square test and Cramer's V on a root-cause vs fix co-occurrence matrix CSV."
        )
    )
    parser.add_argument(
        "--input-root-cause-fix",
        type=Path,
        default=Path("plots/cooccurrence_matrix_root_cause_fix.csv"),
        help="Root-cause vs fix co-occurrence matrix CSV.",
    )
    parser.add_argument(
        "--input-fix-ap",
        type=Path,
        default=Path("dataset/bugs/dataset_fixes_ap_abs.csv"),
        help="Fix vs anti-pattern co-occurrence matrix CSV (absolute counts).",
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance level alpha (default: 0.05).",
    )
    parser.add_argument(
        "--n-bootstrap",
        type=int,
        default=5000,
        help="Number of bootstrap samples for Cramer's V CI (default: 5000).",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.95,
        help="Confidence level for Cramer's V interval (default: 0.95).",
    )
    parser.add_argument(
        "--pvalue-threshold",
        type=float,
        default=0.0001,
        help="Display p-value as '< threshold' when smaller (default: 0.0001).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for bootstrap sampling (default: 42).",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.input_root_cause_fix.exists():
        raise FileNotFoundError(f"Input file not found: {args.input_root_cause_fix}")
    if not args.input_fix_ap.exists():
        raise FileNotFoundError(f"Input file not found: {args.input_fix_ap}")
    if args.alpha <= 0 or args.alpha >= 1:
        raise ValueError("alpha must be between 0 and 1.")
    if args.n_bootstrap < 100:
        raise ValueError("n-bootstrap must be >= 100.")
    if args.confidence <= 0 or args.confidence >= 1:
        raise ValueError("confidence must be between 0 and 1.")
    if args.pvalue_threshold <= 0:
        raise ValueError("pvalue-threshold must be > 0.")

    run_analysis(
        input_csv=args.input_root_cause_fix,
        relation_name="Root Cause Groups vs Fix Groups",
        alpha=args.alpha,
        n_bootstrap=args.n_bootstrap,
        confidence=args.confidence,
        pvalue_threshold=args.pvalue_threshold,
        random_seed=args.seed,
    )
    print("")
    run_analysis(
        input_csv=args.input_fix_ap,
        relation_name="Fix Groups vs Anti-Patterns",
        alpha=args.alpha,
        n_bootstrap=args.n_bootstrap,
        confidence=args.confidence,
        pvalue_threshold=args.pvalue_threshold,
        random_seed=args.seed + 1,
    )


if __name__ == "__main__":
    main()
