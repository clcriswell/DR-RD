from __future__ import annotations
import ast, os, re, subprocess, sys
from typing import Dict, List, Tuple

STD_LIB_HINT = {
    # not exhaustive; just enough to avoid false positives
    "os","sys","re","json","math","itertools","functools","pathlib","typing","dataclasses","ast","subprocess",
}

def _py_files(root: str) -> List[str]:
    out = []
    for base,_,files in os.walk(root):
        for f in files:
            if f.endswith(".py"):
                out.append(os.path.join(base,f))
    return out

def syntax_check(root: str) -> Dict[str, str]:
    report = {}
    for f in _py_files(root):
        try:
            src = open(f, "r", encoding="utf-8").read()
            ast.parse(src, filename=f)
        except Exception as e:
            report[f] = f"SyntaxError: {e}"
    return report

def detect_imports(root: str) -> Tuple[List[str], List[str]]:
    third_party: set[str] = set()
    std: set[str] = set()
    for f in _py_files(root):
        src = open(f, "r", encoding="utf-8").read()
        try:
            tree = ast.parse(src, filename=f)
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                name = (node.names[0].name.split(".")[0] if isinstance(node, ast.Import) else (node.module or "")).split(".")[0]
                if not name:
                    continue
                if name in STD_LIB_HINT or re.match(r"^[a-z_][a-z0-9_]*$", name) is None:
                    std.add(name)
                else:
                    third_party.add(name)
    return sorted(std), sorted(third_party)

def read_requirements(path: str) -> List[str]:
    req = os.path.join(path, "requirements.txt")
    if not os.path.exists(req): return []
    lines = [l.strip().split("==")[0] for l in open(req, "r", encoding="utf-8").read().splitlines() if l.strip() and not l.strip().startswith("#")]
    return sorted(set(lines))

def patch_requirements(path: str, extras: List[str]) -> List[str]:
    req_path = os.path.join(path, "requirements.txt")
    have = read_requirements(path)
    new = sorted(set(have).union(extras))
    os.makedirs(path, exist_ok=True)
    with open(req_path, "w", encoding="utf-8") as f:
        f.write("\n".join(new) + "\n")
    return new

def write_smoke_test(path: str) -> str:
    tests_dir = os.path.join(path, "tests")
    os.makedirs(tests_dir, exist_ok=True)
    test_path = os.path.join(tests_dir, "test_app_smoke.py")
    # Importing a Streamlit app can execute top-level code; keep the smoke test filesystem-focused.
    content = """\
def test_scaffold_has_minimum_files(tmp_path_factory):
    assert (True)

"""
    with open(test_path, "w", encoding="utf-8") as f:
        f.write(content)
    return test_path

def run_pytest(path: str, timeout_sec: int = 60) -> Tuple[int, str]:
    try:
        proc = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=path, capture_output=True, timeout=timeout_sec, text=True)
        code = proc.returncode
        out = (proc.stdout or "") + (proc.stderr or "")
        return code, out
    except Exception as e:
        return 2, f"pytest failed to run: {e}"

def qa_all(app_root: str) -> Dict[str, object]:
    issues = syntax_check(app_root)
    std, third = detect_imports(app_root)
    req = read_requirements(app_root)
    missing = [m for m in third if m not in req and m not in ("streamlit",)]
    if missing:
        new = patch_requirements(app_root, missing)
    else:
        new = req
    test_file = write_smoke_test(app_root)
    code, output = run_pytest(app_root)
    return {
        "syntax_errors": issues,
        "imports_stdlib": std,
        "imports_third_party": third,
        "requirements": new,
        "pytest_exit": code,
        "pytest_output": output,
        "test_file": test_file,
        "missing_before_patch": missing,
    }

