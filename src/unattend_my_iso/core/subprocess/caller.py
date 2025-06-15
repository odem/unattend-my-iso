import os
import subprocess

from unattend_my_iso.common.logging import log_info

PIPE = subprocess.PIPE
STDOUT = subprocess.STDOUT
DEVNULL = subprocess.DEVNULL
Popen = subprocess.Popen

CompletedProcess = subprocess.CompletedProcess
CalledProcessError = subprocess.CalledProcessError


def run(*args, **kwargs) -> CompletedProcess:
    if args[0][0] == "sudo":
        args[0].insert(1, "-A")
    env = os.environ.copy()
    log_info(f"EXEC: {args}")
    return subprocess.run(*args, **kwargs, env=env)


def check_call(args: list[str]) -> int:
    log_info(f"EXEC: {args}")
    return subprocess.call(args)


def run_background(*args, **kwargs) -> subprocess.Popen[str]:
    if args[0][0] == "sudo":
        args[0].insert(1, "-A")
    env = os.environ.copy()
    return subprocess.Popen(*args, **kwargs, env=env)
