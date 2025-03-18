from dataclasses import dataclass


@dataclass
class TaskResult:
    success: bool
    msg: str
    msg_short: str
    msg_out: str
    msg_err: str
