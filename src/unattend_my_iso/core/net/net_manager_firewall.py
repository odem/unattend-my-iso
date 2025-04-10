import subprocess
from unattend_my_iso.common.logging import log_debug, log_error


class FirewallManager:
    def __init__(self):
        pass

    def has_masquerading(self, name: str) -> bool:
        try:
            ret = subprocess.run(
                ["sudo", "iptables", "-t", "nat", "-L", "POSTROUTING", "-n", "-v"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            for line in ret.stdout.splitlines():
                if "MASQUERADE" in line and name in line:
                    return True
        except subprocess.CalledProcessError as e:
            log_error(f"Error checking {name}: {e}", self.__class__.__qualname__)
        return False

    def add_masquerading(self, name: str) -> bool:
        if self.has_masquerading(name):
            return True
        try:
            subprocess.run(
                [
                    "sudo",
                    "iptables",
                    "-t",
                    "nat",
                    "-A",
                    "POSTROUTING",
                    "-o",
                    name,
                    "-j",
                    "MASQUERADE",
                ],
                check=True,
            )
            log_debug(
                f"Added masquerading on {name}",
                self.__class__.__qualname__,
            )
        except subprocess.CalledProcessError as e:
            log_error(f"Error creating {name}: {e}", self.__class__.__qualname__)
            return False
        return True

    def del_masquerading(self, name: str) -> bool:
        if self.has_masquerading(name) is False:
            return True
        try:
            subprocess.run(
                [
                    "sudo",
                    "iptables",
                    "-t",
                    "nat",
                    "-D",
                    "POSTROUTING",
                    "-o",
                    name,
                    "-j",
                    "MASQUERADE",
                ],
                check=True,
            )
            log_debug(
                f"Deleted masquerading on {name}",
                self.__class__.__qualname__,
            )
        except subprocess.CalledProcessError as e:
            log_error(f"Error creating {name}: {e}", self.__class__.__qualname__)
            return False
        return True

    def add_masqueradings(self, brlists: list[list[str]]) -> bool:
        for brlist in brlists:
            if len(brlists) == 4:
                name = brlist[0]
                masq = brlist[3]
                if masq is True:
                    if self.add_masquerading(name) is False:
                        return False
        return True

    def del_masqueradings(self, brlists: list[list[str]]) -> bool:
        for brlist in brlists:
            if len(brlists) == 4:
                name = brlist[0]
                masq = brlist[3]
                if masq is True:
                    if self.del_masquerading(name) is False:
                        return False
        return True
