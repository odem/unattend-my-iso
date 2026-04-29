import os
import sys
import importlib.util
from pathlib import Path


def run():
    script_path = Path(__file__).resolve()

    # Go up to repo root, then into src
    project_root = script_path.parents[2]   # unattend-my-iso/
    src_path = project_root / "src"

    sys.path.insert(0, str(src_path))  # <-- KEY FIX

    print(f"CWD: {os.getcwd()}")
    print(f"sys.path[0]: {sys.path[0]}")

    script_path = Path(__file__).resolve()
    module_path = script_path.parent / "main.py"
    spec = importlib.util.spec_from_file_location("main", module_path)
    if spec is not None and spec.loader is not None:
        loaded_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(loaded_module)
        loaded_module.main(debug=True)


run()
