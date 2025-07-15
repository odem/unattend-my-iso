import importlib.util
from pathlib import Path


def run():
    script_path = Path(__file__).resolve()
    module_path = script_path.parent / "main.py"
    spec = importlib.util.spec_from_file_location("main", module_path)
    if spec is not None and spec.loader is not None:
        loaded_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(loaded_module)
        loaded_module.main(debug=True)


run()
