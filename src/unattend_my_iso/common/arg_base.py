from typing import Any


class ArgumentBase:
    def get_config_values(self) -> dict[str, Any]:
        result = {}
        for el in vars(self):
            val = self.__dict__[el]
            result[f"CFG_{el.upper()}"] = val
        return result

    def get_env_vars_bash(self) -> list[str]:
        result = []
        values = self.get_config_values()
        for key, val in values.items():
            if isinstance(val, dict):
                normlist = self.normalize_dict_bash(val)
                for normentry in normlist:
                    result.append(normentry)
            else:
                normval = self.normalize_value_bash(val)
                result.append(f"export {key}={normval}")
        return result

    def get_env_vars_batch(self) -> list[str]:
        result = []
        values = self.get_config_values()
        for key, val in values.items():
            if isinstance(val, list):
                normlist = self.normalize_listvalue_batch(key, val)
                for normentry in normlist:
                    result.append(normentry)
            elif isinstance(val, dict):
                normlist = self.normalize_dict_batch(val)
                for normentry in normlist:
                    result.append(normentry)
            else:
                normval = self.normalize_value_batch(val)
                result.append(f"set {key}={normval}")
        return result

    def normalize_value_bash(self, val: Any) -> str:
        if isinstance(val, bool):
            return "1" if val is True else "0"
        elif isinstance(val, str):
            return f'"{val}"'
        elif isinstance(val, int):
            return str(val)
        elif isinstance(val, tuple):
            return f'"{val[0]},{val[1]}"'
        elif isinstance(val, list):
            result = ["("]
            for listval in val:
                if isinstance(listval, list):
                    strlist = str(listval).removeprefix("[").removesuffix("]")
                    normval = f'"{strlist}"'
                else:
                    normval = self.normalize_value_bash(listval)
                result.append(normval)
            result += [")"]
            return " ".join(result)
        else:
            return str(val)

    def normalize_listvalue_batch(self, key: str, val: Any) -> list[str]:
        result = []
        if isinstance(val, list):
            for x in range(len(val)):
                listval = val[x]
                if isinstance(listval, list):
                    normval = self.normalize_listvalue_batch(key, listval)
                else:
                    normval = self.normalize_value_batch(listval)
                result.append(f"set {key}[{x}]={normval}")
        return result

    def normalize_value_batch(self, val: Any) -> str:
        if isinstance(val, bool):
            return "1" if val is True else "0"
        elif isinstance(val, str):
            return f"{val}"
        elif isinstance(val, int):
            return str(val)
        elif isinstance(val, tuple):
            return f"{val[0]},{val[1]}"
        else:
            return str(val)

    def normalize_dict_bash(self, val: Any) -> list[str]:
        if isinstance(val, dict):
            result = []
            for key, innerval in val.items():
                normval = self.normalize_value_bash(innerval)
                result.append(f"export {key}={normval}")
            return result
        else:
            return []

    def normalize_list_batch(self, key: str, val: Any) -> list[str]:
        if isinstance(val, list):
            result = []
            for x in range(len(val)):
                innerval = val[x]
                listkey = f"{key}[{x}]"
                result += self.normalize_listvalue_batch(listkey, innerval)
            return result
        else:
            return []

    def normalize_dict_batch(self, val: Any) -> list[str]:
        if isinstance(val, dict):
            result = []
            for key, innerval in val.items():
                normval = self.normalize_value_batch(innerval)
                result.append(f"set {key}={normval}")
            return result
        else:
            return []
