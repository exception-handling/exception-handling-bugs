"""
For every commit in the dataset, runs the ast-based detector on the
BEFORE (commit~1) and AFTER (commit) state of every changed .py file.

Outputs:
  fixes_val/miner_before.csv  — function-level AP counts at commit~1
  fixes_val/miner_after.csv   — function-level AP counts at commit
  fixes_val/mine_commits_errors.log

Each row: project, commit_fix, file, function, func_body,
          n_bare_except, n_generic_except, n_captures_broad_raise,
          n_try_pass, n_bare_raise_finally,
          n_captures_misplaced_bare_raise, n_nested_try
"""

import os
import subprocess
import sys
import pandas as pd
from tqdm import tqdm

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fixes_val.detector import parse_functions

DATASET   = "dataset/bugs/dataset_exception_fixes_anti_patterns.csv"
CLONE_DIR = "projects/py"
OUT_BEFORE = "fixes_val/miner_before.csv"
OUT_AFTER  = "fixes_val/miner_after.csv"
LOG_FILE   = "fixes_val/mine_commits_errors.log"

AP_COLS = [
    "n_bare_except", "n_generic_except", "n_captures_broad_raise",
    "n_try_pass", "n_bare_raise_finally",
    "n_captures_misplaced_bare_raise", "n_nested_try",
]


def git_show(repo_path: str, ref: str, filepath: str) -> str | None:
    """Return file content at `ref` in `repo_path`, or None if not found."""
    result = subprocess.run(
        ["git", "show", f"{ref}:{filepath}"],
        capture_output=True, text=True, cwd=repo_path
    )
    return result.stdout if result.returncode == 0 else None


def changed_py_files(repo_path: str, commit: str) -> list[str]:
    """Return .py files changed between commit~1 and commit."""
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{commit}~1", commit],
        capture_output=True, text=True, cwd=repo_path
    )
    if result.returncode != 0:
        return []
    return [f for f in result.stdout.splitlines() if f.endswith(".py")]


def mine_source(project, commit, filepath, source) -> list[dict]:
    rows = []
    for func in parse_functions(source):
        row = {"project": project, "commit_fix": commit, "file": filepath}
        row.update(func)
        rows.append(row)
    return rows


df = pd.read_csv(DATASET)
commits = df[["project", "commit_fix"]].drop_duplicates()
print(f"Commits to process: {len(commits)}")

before_rows, after_rows, errors = [], [], []

for _, rec in tqdm(commits.iterrows(), total=len(commits)):
    project = str(rec["project"])
    commit  = str(rec["commit_fix"])
    repo    = os.path.join(CLONE_DIR, project)

    if not os.path.isdir(repo):
        errors.append(f"MISSING_REPO  {project}  {commit}")
        continue

    py_files = changed_py_files(repo, commit)
    if not py_files:
        errors.append(f"NO_PY_FILES  {project}  {commit}")
        continue

    for fpath in py_files:
        src_before = git_show(repo, f"{commit}~1", fpath)
        src_after  = git_show(repo, commit, fpath)

        if src_before:
            before_rows.extend(mine_source(project, commit, fpath, src_before))
        if src_after:
            after_rows.extend(mine_source(project, commit, fpath, src_after))

cols = ["project", "commit_fix", "file", "function", "func_body"] + AP_COLS
pd.DataFrame(before_rows, columns=cols if before_rows else None).to_csv(OUT_BEFORE, index=False)
pd.DataFrame(after_rows,  columns=cols if after_rows  else None).to_csv(OUT_AFTER,  index=False)

with open(LOG_FILE, "w") as f:
    f.write("\n".join(errors))

print(f"\nBefore rows: {len(before_rows)}  →  {OUT_BEFORE}")
print(f"After  rows: {len(after_rows)}   →  {OUT_AFTER}")
print(f"Errors: {len(errors)}  (see {LOG_FILE})")
