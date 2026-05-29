"""
Adjusted standardized residuals for the domain × root_cause_grp contingency table.

Computes Haberman (1973) adjusted residuals:
    z_ij = (O_ij - E_ij) / sqrt(E_ij * (1 - R_i/n) * (1 - C_j/n))

Under H0 each z_ij ~ N(0,1), so |z| > 1.96 flags a cell as significantly
over- or under-represented at alpha = 0.05.

Outputs:
    experiment_val/dataset/domain_rootcause_residuals.csv   -- z-scores
    experiment_val/dataset/domain_rootcause_counts.csv      -- observed counts
    experiment_val/dataset/domain_rootcause_pct.csv         -- row percentages
"""

import pathlib
import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency

DATASET = pathlib.Path(__file__).parent.parent / "dataset/bugs/dataset_exception_bugs_with_domain.csv"
OUT_DIR  = pathlib.Path(__file__).parent / "dataset"
OUT_DIR.mkdir(exist_ok=True)

MIN_DOMAIN_N = 10   # drop domains with fewer bugs (sparse rows)

DOMAIN_LABELS = {
    "Data Science, Machine Learning & AI":          "ML & AI",
    "DevOps, Cloud & Infrastructure":               "DevOps/Cloud",
    "Developer Tools & Libraries":                  "Dev Tools",
    "End-user Applications & Systems":              "End-user Apps",
    "Scientific & Numerical Computing":             "Scientific",
    "Security, Networking & Reverse Engineering":   "Security/Net",
    "Web Development & APIs":                       "Web APIs",
    "Testing, QA & Benchmarking":                   "Testing/QA",
}

RC_LABELS = {
    "API-Related Exception Handling Errors":  "API-Related",
    "Import-Related Exception":               "Import-Related",
    "Improper Exception Message":             "Improper Msg",
    "Improper Finally Block Usage":           "Finally Block",
    "Incorrect Handling Action":              "Incorrect Action",
    "Incorrect Re-raising of Exceptions":     "Incorrect Re-raise",
    "Missing Exception Raising Condition":    "Missing Raise Cond.",
    "Python Version Compatibility Issue":     "Py Version Compat.",
    "Unexpected Raising":                     "Unexpected Raising",
    "Unhandled Exception":                    "Unhandled Exc.",
    "Wrong Exception Type":                   "Wrong Exc. Type",
    "Wrong Raise Type":                       "Wrong Raise Type",
}


def load_bugs(path: pathlib.Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df[df["exception_bug"] == "Y"].copy()
    df["root_cause_grp"] = df["root_cause_grp"].str.strip()
    return df


def build_contingency(df: pd.DataFrame, min_domain_n: int) -> pd.DataFrame:
    ct = pd.crosstab(df["domain"], df["root_cause_grp"])
    ct = ct[ct.sum(axis=1) >= min_domain_n]
    return ct


def adjusted_residuals(ct: pd.DataFrame) -> pd.DataFrame:
    """Return a DataFrame of Haberman adjusted standardised residuals."""
    obs = ct.values.astype(float)
    _, _, _, expected = chi2_contingency(obs, correction=False)
    n = obs.sum()
    row_totals = obs.sum(axis=1, keepdims=True)
    col_totals = obs.sum(axis=0, keepdims=True)
    denom = np.sqrt(expected * (1 - row_totals / n) * (1 - col_totals / n))
    z = (obs - expected) / denom
    return pd.DataFrame(z, index=ct.index, columns=ct.columns)


def relabel(df: pd.DataFrame, row_map: dict, col_map: dict) -> pd.DataFrame:
    df = df.copy()
    df.index = [row_map.get(i, i) for i in df.index]
    df.columns = [col_map.get(c, c) for c in df.columns]
    return df


def chi2_summary(ct: pd.DataFrame) -> dict:
    chi2, p, dof, _ = chi2_contingency(ct.values, correction=False)
    return {"chi2": round(chi2, 2), "p_value": round(p, 4), "dof": dof}


def main():
    df   = load_bugs(DATASET)
    ct   = build_contingency(df, MIN_DOMAIN_N)
    z_df = adjusted_residuals(ct)
    pct  = ct.div(ct.sum(axis=1), axis=0).mul(100).round(1)

    stats = chi2_summary(ct)
    print(f"Chi-square: chi2={stats['chi2']}, p={stats['p_value']}, dof={stats['dof']}")
    print(f"Domains: {ct.shape[0]} | Root causes: {ct.shape[1]} | Exception bugs: {int(ct.values.sum())}")

    # apply short labels
    ct_out  = relabel(ct,   DOMAIN_LABELS, RC_LABELS)
    z_out   = relabel(z_df, DOMAIN_LABELS, RC_LABELS)
    pct_out = relabel(pct,  DOMAIN_LABELS, RC_LABELS)

    # add row totals
    ct_out["Total"]  = ct_out.sum(axis=1)
    pct_out["Total"] = pct_out.sum(axis=1).round(1)

    ct_out.index.name  = "Domain"
    z_out.index.name   = "Domain"
    pct_out.index.name = "Domain"

    ct_out.to_csv(OUT_DIR  / "domain_rootcause_counts.csv")
    z_out.round(2).to_csv(OUT_DIR / "domain_rootcause_residuals.csv")
    pct_out.to_csv(OUT_DIR / "domain_rootcause_pct.csv")

    print(f"\nFiles written to {OUT_DIR}/")
    print("  domain_rootcause_counts.csv")
    print("  domain_rootcause_residuals.csv")
    print("  domain_rootcause_pct.csv")

    print("\n=== Significant cells (|z| > 1.96) ===")
    for domain in z_out.index:
        for rc in z_out.columns:
            z = z_out.loc[domain, rc]
            if abs(z) > 1.96:
                obs = ct_out.loc[domain, rc]
                sign = "over" if z > 0 else "under"
                print(f"  [{sign:5s}] {domain} | {rc}: z={z:+.2f} (n={obs})")


if __name__ == "__main__":
    main()
