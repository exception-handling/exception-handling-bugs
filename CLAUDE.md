# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Research tool for mining and analyzing exception handling patterns in Python codebases, accompanying the paper *"Slithering Through Exception Handling Bugs in Python: Understanding Symptoms, Root Causes, Fixes and Anti-patterns"*. It parses Python source files with tree-sitter, extracts per-function exception handling metrics, and uses PyCG call graphs to detect uncaught exception propagation.

## Commands

**Setup** (one-time):
```bash
pip install -r requirements.txt
# tree-sitter-python grammar must be cloned manually (it's gitignored):
git clone https://github.com/tree-sitter/tree-sitter-python
```

**Run the miner** (clones projects from `projects_py.csv`, outputs to `output/parser/`):
```bash
python3 miner.py
```

**Tests:**
```bash
python3 -m unittest                          # all tests
python3 -m unittest tests.test_miner_py_utils  # single test file
python3 -m unittest tests.test_miner_py_utils.TestCounters.test_count_raise  # single test
```

**Coverage:**
```bash
coverage run -m unittest
coverage report --omit *test_*,*__init__*
```

**Inter-rater agreement** (for dataset validation):
```bash
python3 experiment_val/agreement.py
```

## Architecture

### Startup side-effect in `tree_sitter_lang.py`
On import, `miner_py_src/tree_sitter_lang.py` calls `Language.build_library(...)` which compiles `tree-sitter-python/` into `build/my-languages.so`. This means **the `tree-sitter-python` directory must exist before any import of `miner_py_src`**. All tree-sitter `Query` objects (e.g. `QUERY_TRY_STMT`, `QUERY_EXCEPT_CLAUSE`) are module-level constants defined here and imported across the package.

### Pipeline flow (`miner.py`)
1. `fetch_repositories()` — clones a project and returns its `.py` file paths via PyDriller/GitPython.
2. `collect_parser()` — iterates over files, parses each with tree-sitter, queries all `function_definition` nodes, and calls `FileStats.get_metrics()` on each. Results accumulate in a pandas DataFrame.
3. `generate_cfg()` (in `call_graph.py`) — shells out to `pycg` for the whole project, reads the resulting JSON, and builds a bidirectional adjacency dict (`calls` / `called_by`).
4. The `CFG` class is then used to walk the call graph and annotate functions whose raised exceptions are not caught by their callers, writing `str_uncaught_exceptions` back into the DataFrame.
5. Output is written to `output/parser/<project_name>_stats.csv`.

### PyCG naming convention
Functions in PyCG's output starting with `...` are project-internal (e.g. `...mymodule.MyClass.method`). Functions with only one component after `...` are built-ins and are skipped. The miner maps `...module.path.func` to file paths by converting dots to slashes.

### `miner_py_src/` package
- **`miner_py_utils.py`** — all tree-sitter query logic. Functions accept `tree_sitter.binding.Node` and return counts or lists. This is where detection of anti-patterns lives (bare except, generic except, misplaced bare raise, broad exception raised, etc.).
- **`stats.py`** — `FileStats.get_metrics(func_def_node)` collects all per-function metrics into a dict for the CSV. Also contains `TBLDStats` and `CBGDStats` for token/statement statistics used in separate analyses.
- **`call_graph.py`** — `generate_cfg()` wraps `pycg` subprocess; `CFG.get_uncaught_exceptions()` performs a single-level call-graph traversal to find callers that don't catch the raised types.
- **`exceptions.py`** — custom exception hierarchy rooted at `MinerPyError`.
- **`builtin.py`** — reference-only comment showing Python's built-in exception hierarchy.

### Dataset
- `dataset/bugs/dataset_exception_bugs.csv` — main dataset (bugs, root causes, fixes).
- `dataset/bugs/dataset_exception_fixes_anti_patterns.csv` — fixes mapped to anti-patterns.
- `projects_py.csv` — list of GitHub projects to mine (`name`, `repo` columns).
- `experiment_val/` — inter-rater agreement scripts using Cohen's Kappa and Krippendorff's alpha.
