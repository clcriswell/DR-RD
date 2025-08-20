import json, importlib, pkgutil, inspect
paths = ["core.agents"]
inventory = {}
def collect(pkg_name):
    try:
        pkg = importlib.import_module(pkg_name)
    except Exception:
        return
    for _, modname, _ in pkgutil.walk_packages(pkg.__path__, pkg_name + "."):
        try:
            m = importlib.import_module(modname)
        except Exception:
            continue
        for _, obj in inspect.getmembers(m, inspect.isclass):
            if getattr(obj, "run", None):
                role = getattr(obj, "ROLE", None) or getattr(obj, "NAME", None) or obj.__name__
                inventory.setdefault(pkg_name, []).append({"role": role, "class": f"{obj.__module__}.{obj.__name__}"})
for p in paths: collect(p)
print(json.dumps(inventory, indent=2))
