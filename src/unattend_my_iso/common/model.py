from dataclasses import dataclass


@dataclass
class Replaceable:
    filename: str
    searchterm: str
    replacement: str
