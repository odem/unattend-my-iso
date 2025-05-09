from dataclasses import dataclass


@dataclass
class Replaceable:
    filename: str
    searchterm: str
    replacement: str | bool


@dataclass
class PartitionFlag:
    name: str
    value: str = ""

    def __str__(self) -> str:
        format_val = " "
        if self.value != "":
            format_val = f" {self.value} "
        return f"{self.name}{{{format_val}}}"


@dataclass
class RecipeDescription:
    sizes: list[str | int]
    use_type: str
    mountpoint: str
    name_vg: str = ""
    name_lv: str = ""
    label: str = ""
    iflabel: str = ""


@dataclass
class DIOption:
    name: str
    value: str | bool | list[str] = ""
    _type: str = "string"
    _prefix: str = "d-i"

    def __str__(self) -> str:
        ret = []
        if isinstance(self.value, bool):
            ret = [
                self._prefix,
                self.name,
                "boolean",
                "true" if self.value is True else "false",
            ]
        elif isinstance(self.value, list):
            ret = [
                self._prefix,
                self.name,
                "multiselect",
                ", \\\n    ".join(self.value),
            ]
        elif self.name == "#":
            ret = [f"\n{self.name}", self.value]
        elif self._type in ("string", "password", "select", "note"):
            ret = [self._prefix, self.name, self._type, self.value]
        else:
            ret = ["ERROR!"]
        return " ".join(ret)
