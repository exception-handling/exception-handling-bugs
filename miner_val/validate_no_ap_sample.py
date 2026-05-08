"""
Independently validates no_antipattern_sample.csv using Python's ast module.
Produces no_antipattern_sample_validated.csv with columns:
  project, file, function, func_body, anti_pattern, confidence_level, has_ap
"""

import ast
import textwrap
import pandas as pd

INPUT_CSV  = "miner_val/no_antipattern_sample.csv"
OUTPUT_CSV = "miner_val/no_antipattern_sample_validated.csv"

AP_BARE_EXCEPT   = "Bare Except Catch Block"
AP_BROAD_EXCEPT  = "Too Broad Except"
AP_BROAD_RAISE   = "Too Broad Raising"
AP_SWALLOW       = "Swallowing Exceptions"
AP_BARE_FINALLY  = "Bare Raise inside Finally"
AP_BARE_RAISE    = "Bare Raise Block"
AP_NESTED_TRY    = "Nested Try-Except Blocks"

BROAD_NAMES = {"Exception", "BaseException"}


# ── AST helpers ──────────────────────────────────────────────────────────────

def _bare_raise_in_stmts(stmts):
    """True if any bare 'raise' exists in the statement list (no recursion into Try)."""
    for node in ast.walk(ast.Module(body=stmts, type_ignores=[])):
        if isinstance(node, ast.Raise) and node.exc is None:
            return True
    return False


def _max_try_depth(node, depth=0):
    """Recursively compute maximum nested try depth."""
    max_d = depth
    children = (
        list(node.body if hasattr(node, 'body') else []) +
        list(node.orelse if hasattr(node, 'orelse') else []) +
        list(node.finalbody if hasattr(node, 'finalbody') else []) +
        list(node.handlers if hasattr(node, 'handlers') else [])
    )
    for child in children:
        if isinstance(child, ast.Try):
            max_d = max(max_d, _max_try_depth(child, depth + 1))
        elif hasattr(child, '__dict__'):
            max_d = max(max_d, _max_try_depth(child, depth))
    return max_d


class _Detector(ast.NodeVisitor):
    def __init__(self):
        self.found = []

    def visit_Try(self, node):
        # Bare Except / Too Broad Except / Swallowing
        for h in node.handlers:
            if h.type is None:
                self.found.append(AP_BARE_EXCEPT)
            elif isinstance(h.type, ast.Name) and h.type.id in BROAD_NAMES:
                self.found.append(AP_BROAD_EXCEPT)
            elif isinstance(h.type, ast.Tuple):
                for elt in h.type.elts:
                    if isinstance(elt, ast.Name) and elt.id in BROAD_NAMES:
                        self.found.append(AP_BROAD_EXCEPT)

            body_stmts = [s for s in h.body if not isinstance(s, ast.Pass)]
            if not body_stmts:
                self.found.append(AP_SWALLOW)

        # Bare Raise inside Finally
        for stmt in node.finalbody:
            if _bare_raise_in_stmts([stmt]):
                self.found.append(AP_BARE_FINALLY)
                break

        self.generic_visit(node)

    def visit_Raise(self, node):
        # Too Broad Raising
        exc = node.exc
        if exc is not None:
            name = None
            if isinstance(exc, ast.Name):
                name = exc.id
            elif isinstance(exc, ast.Call) and isinstance(exc.func, ast.Name):
                name = exc.func.id
            if name in BROAD_NAMES:
                self.found.append(AP_BROAD_RAISE)

        self.generic_visit(node)


def _detect_bare_raise_block(tree):
    """
    Bare raise outside an except handler.
    Walk the tree; when we enter an except handler body we stop tracking.
    """
    found = []

    def walk(nodes, in_except=False):
        for node in nodes:
            if isinstance(node, ast.Try):
                walk(node.body, in_except=False)
                for h in node.handlers:
                    walk(h.body, in_except=True)
                walk(node.orelse, in_except=False)
                walk(node.finalbody, in_except=False)
            elif isinstance(node, ast.Raise):
                if node.exc is None and not in_except:
                    found.append(AP_BARE_RAISE)
            else:
                child_stmts = []
                for field, value in ast.iter_fields(node):
                    if isinstance(value, list):
                        child_stmts.extend(v for v in value if isinstance(v, ast.AST))
                    elif isinstance(value, ast.AST):
                        child_stmts.append(value)
                walk(child_stmts, in_except=in_except)

    walk(tree.body)
    return found


def detect(func_body: str):
    """
    Returns (anti_patterns: list[str], confidence_level: str).
    confidence_level is 'absolute' when ast parsed cleanly, 'low' on parse failure.
    """
    src = textwrap.dedent(func_body)
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return [], "low"

    detector = _Detector()
    detector.visit(tree)
    found = list(dict.fromkeys(detector.found))  # deduplicate, preserve order

    found += _detect_bare_raise_block(tree)

    # Nested try: 3+ levels
    for node in ast.walk(tree):
        if isinstance(node, ast.Try):
            if _max_try_depth(node) >= 3:
                found.append(AP_NESTED_TRY)
                break

    found = list(dict.fromkeys(found))
    return found, "absolute"


# ── Main ─────────────────────────────────────────────────────────────────────

df = pd.read_csv(INPUT_CSV)

rows = []
for _, row in df.iterrows():
    patterns, confidence = detect(str(row["func_body"]))
    has_ap = "Y" if patterns else "N"
    anti_pattern = ", ".join(patterns) if patterns else ""
    rows.append({
        "project":          row["project"],
        "file":             row["file"],
        "function":         row["function"],
        "func_body":        row["func_body"],
        "anti_pattern":     anti_pattern,
        "confidence_level": confidence,
        "has_ap":           has_ap,
    })

out = pd.DataFrame(rows)
out.to_csv(OUTPUT_CSV, index=False)

total     = len(out)
has_ap_y  = (out["has_ap"] == "Y").sum()
low_conf  = (out["confidence_level"] == "low").sum()
print(f"Total functions : {total}")
print(f"has_ap = Y      : {has_ap_y}")
print(f"has_ap = N      : {total - has_ap_y}")
print(f"confidence=low  : {low_conf}  (parse failures)")
if has_ap_y:
    print("\nUnexpected anti-patterns found:")
    print(out[out["has_ap"] == "Y"][["project","function","anti_pattern"]].to_string())
print(f"\nSaved to {OUTPUT_CSV}")
