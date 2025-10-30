import os
import subprocess

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
    return subprocess.run(*args, **kwargs, env=env)


def check_call(args: list[str], **kwargs) -> int:
    return subprocess.call(args, **kwargs)


def run_background(*args, **kwargs) -> subprocess.Popen[str]:
    if args[0][0] == "sudo":
        args[0].insert(1, "-A")
    env = os.environ.copy()
    return subprocess.Popen(*args, **kwargs, env=env)
