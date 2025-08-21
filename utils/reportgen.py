from jinja2 import Environment, FileSystemLoader, select_autoescape
import os, csv

def _env():
    path = os.path.join(os.path.dirname(__file__), "..", "templates")
    return Environment(loader=FileSystemLoader(path), autoescape=select_autoescape())

def render(name: str, ctx: dict) -> str:
    return _env().get_template(name).render(**ctx)

def write_csv(path, rows: list[dict], headers: list[str]):
    import pathlib
    pathlib.Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        [w.writerow(r) for r in rows]
