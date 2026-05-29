"""
Clones all repos referenced in dataset_exception_fixes_anti_patterns.csv
into projects/py/ using blobless clones (--filter=blob:none) to minimise
disk usage while still allowing `git show <commit>:<file>` lookups.

Already-cloned repos are skipped. Failed clones are logged to
fixes_val/clone_errors.log.
"""

import os
import subprocess
import pandas as pd

DATASET   = "dataset/bugs/dataset_exception_fixes_anti_patterns.csv"
CLONE_DIR = "projects/py"
LOG_FILE  = "fixes_val/clone_errors.log"

os.makedirs(CLONE_DIR, exist_ok=True)

df = pd.read_csv(DATASET)
repos = df[["project", "repo_url"]].drop_duplicates()
print(f"Repos to clone: {len(repos)}")

errors = []
for _, row in repos.iterrows():
    project  = str(row["project"])
    repo_url = str(row["repo_url"])
    dest     = os.path.join(CLONE_DIR, project)

    if os.path.isdir(dest):
        print(f"  [skip]  {project}")
        continue

    print(f"  [clone] {project}  ({repo_url})")
    result = subprocess.run(
        ["git", "clone", "--filter=blob:none", f"{repo_url}.git", dest],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        msg = f"{project}: {result.stderr.strip()}"
        print(f"    ERROR: {msg}")
        errors.append(msg)

with open(LOG_FILE, "w") as f:
    f.write("\n".join(errors))

print(f"\nDone. Errors: {len(errors)} (see {LOG_FILE})")
