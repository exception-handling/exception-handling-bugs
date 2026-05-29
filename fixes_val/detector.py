"""
Shared ast-based detector that mirrors the miner's 7 AP columns.
Returns per-function metric dicts compatible with the miner's CSV output.
"""

import ast
import textwrap
from typing import Dict, List, Tuple

AP_BARE_EXCEPT  = "Bare Except Catch Block"
AP_BROAD_EXCEPT = "Too Broad Except"
AP_BROAD_RAISE  = "Too Broad Raising"
AP_SWALLOW      = "Swallowing Exceptions"
AP_BARE_FINALLY = "Bare Raise inside Finally"
AP_BARE_RAISE   = "Bare Raise Block"
AP_NESTED_TRY   = "Nested Try-Except Blocks"

BROAD_NAMES = {"Exception", "BaseException"}

EMPTY_COUNTS = {
    "n_bare_except":                    0,
    "n_generic_except":                 0,
    "n_captures_broad_raise":           0,
    "n_try_pass":                       0,
    "n_bare_raise_finally":             0,
    "n_captures_misplaced_bare_raise":  0,
    "n_nested_try":                     0,
}


def _bare_raise_in_stmts(stmts):
    for node in ast.walk(ast.Module(body=stmts, type_ignores=[])):
        if isinstance(node, ast.Raise) and node.exc is None:
            return True
    return False


def _max_try_depth(node, depth=0):
    max_d = depth
    children = (
        list(getattr(node, "body",      []) or []) +
        list(getattr(node, "orelse",    []) or []) +
        list(getattr(node, "finalbody", []) or []) +
        list(getattr(node, "handlers",  []) or [])
    )
    for child in children:
        if isinstance(child, ast.Try):
            max_d = max(max_d, _max_try_depth(child, depth + 1))
        elif hasattr(child, "__dict__"):
            max_d = max(max_d, _max_try_depth(child, depth))
    return max_d


def _count_for_tree(tree: ast.AST) -> Dict[str, int]:
    counts = dict(EMPTY_COUNTS)

    for node in ast.walk(tree):
        if isinstance(node, ast.Try):
            for h in node.handlers:
                if h.type is None:
                    counts["n_bare_except"] += 1
                elif isinstance(h.type, ast.Name) and h.type.id in BROAD_NAMES:
                    counts["n_generic_except"] += 1
                elif isinstance(h.type, ast.Tuple):
                    if any(isinstance(e, ast.Name) and e.id in BROAD_NAMES
                           for e in h.type.elts):
                        counts["n_generic_except"] += 1

                body = [s for s in h.body if not isinstance(s, ast.Pass)]
                if not body:
                    counts["n_try_pass"] += 1

            for stmt in node.finalbody:
                if _bare_raise_in_stmts([stmt]):
                    counts["n_bare_raise_finally"] += 1
                    break

        if isinstance(node, ast.Raise) and node.exc is not None:
            name = None
            if isinstance(node.exc, ast.Name):
                name = node.exc.id
            elif isinstance(node.exc, ast.Call) and isinstance(node.exc.func, ast.Name):
                name = node.exc.func.id
            if name in BROAD_NAMES:
                counts["n_captures_broad_raise"] += 1

    # bare raise outside except handler
    def _walk_bare_raise(nodes, in_except=False):
        for n in nodes:
            if isinstance(n, ast.Try):
                _walk_bare_raise(n.body, False)
                for h in n.handlers:
                    _walk_bare_raise(h.body, True)
                _walk_bare_raise(n.orelse, False)
                _walk_bare_raise(n.finalbody, False)
            elif isinstance(n, ast.Raise):
                if n.exc is None and not in_except:
                    counts["n_captures_misplaced_bare_raise"] += 1
            else:
                children = []
                for _, v in ast.iter_fields(n):
                    if isinstance(v, list):
                        children.extend(x for x in v if isinstance(x, ast.AST))
                    elif isinstance(v, ast.AST):
                        children.append(v)
                _walk_bare_raise(children, in_except)

    _walk_bare_raise(tree.body)

    # nested try: flag if any try contains another try at depth ≥ 2
    for n in ast.walk(tree):
        if isinstance(n, ast.Try) and _max_try_depth(n) >= 2:
            counts["n_nested_try"] += 1
            break

    return counts


def parse_functions(source: str) -> List[Dict]:
    """
    Parse Python source and return one dict per function_definition with:
      function, func_body, n_bare_except, n_generic_except, ...
    Returns [] on SyntaxError.
    """
    try:
        tree = ast.parse(textwrap.dedent(source))
    except SyntaxError:
        return []

    results = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        func_src = ast.get_source_segment(source, node) or ""
        try:
            func_tree = ast.parse(textwrap.dedent(func_src))
        except SyntaxError:
            func_tree = ast.Module(body=[], type_ignores=[])

        counts = _count_for_tree(func_tree)
        row = {"function": node.name, "func_body": func_src}
        row.update(counts)
        results.append(row)

    return results


def has_any_ap(counts: Dict[str, int]) -> bool:
    return any(counts.get(c, 0) > 0 for c in EMPTY_COUNTS)
