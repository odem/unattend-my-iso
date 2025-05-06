from dataclasses import dataclass


@dataclass
class Replaceable:
    filename: str
    searchterm: str
    replacement: str


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
            ret = [self._prefix, self.name, "multiselect", ", ".join(self.value)]
        elif self.name == "#":
            ret = [f"\n{self.name}", self.value]
        elif (
            self._type == "string" or self._type == "password" or self._type == "select"
        ):
            ret = [self._prefix, self.name, self._type, self.value]
        else:
            ret = ["ERROR!"]
        return " ".join(ret)
