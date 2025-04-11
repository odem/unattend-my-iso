import importlib.util
from pathlib import Path
from unattend_my_iso.core.files.file_manager import UmiFileManager


def run():
    files = UmiFileManager()
    cwd_path = Path(f"{files.cwd()}/../..").resolve()
    script_path = Path(__file__).resolve()
    module_path = script_path.parent / "main.py"
    spec = importlib.util.spec_from_file_location("main", module_path)
    if spec is not None and spec.loader is not None:
        loaded_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(loaded_module)
        loaded_module.main(work_path=cwd_path, debug=True)


run()
