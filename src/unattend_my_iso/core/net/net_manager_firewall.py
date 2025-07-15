from unattend_my_iso.core.subprocess.caller import run, CalledProcessError, PIPE
from unattend_my_iso.common.logging import log_debug, log_error


class FirewallManager:
    def __init__(self):
        pass

    def has_masquerading(self, name: str) -> bool:
        try:
            ret = run(
                ["sudo", "iptables", "-t", "nat", "-L", "POSTROUTING", "-n", "-v"],
                stdout=PIPE,
                stderr=PIPE,
                text=True,
            )
            for line in ret.stdout.splitlines():
                if "MASQUERADE" in line and name in line:
                    return True
        except CalledProcessError as e:
            log_error(f"Error checking {name}: {e}", self.__class__.__qualname__)
        return False

    def add_masquerading(self, name: str) -> bool:
        if self.has_masquerading(name):
            return True
        try:
            run(self.create_rule_masq(name, True), check=True)
            log_debug(
                f"Added masquerading on {name}",
                self.__class__.__qualname__,
            )
        except CalledProcessError as e:
            log_error(f"Error creating {name}: {e}", self.__class__.__qualname__)
            return False
        return True

    def del_masquerading(self, name: str) -> bool:
        if self.has_masquerading(name) is False:
            return True
        if name == "":
            log_error(f"No uplink device: {name}", self.__class__.__qualname__)
            return False
        try:
            run(self.create_rule_masq(name, False), check=True)
            log_debug(f"Deleted masquerading on {name}", self.__class__.__qualname__)
        except CalledProcessError as e:
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

    def get_default_route_interfaces(self) -> list[str]:
        try:
            proc = run(
                ["ip", "route", "show", "default"], capture_output=True, text=True
            )
            interfaces = []

            if proc.stdout is not None and proc.stdout != "":
                for line in proc.stdout.strip().splitlines():
                    parts = line.split()
                    if "dev" in parts:
                        dev_index = parts.index("dev") + 1
                        if dev_index < len(parts):
                            interfaces.append(parts[dev_index])
            return interfaces

        except CalledProcessError as e:
            log_error(f"Error running ip route: {e}", self.__class__.__qualname__)
            return []

    def set_ip_forwarding(self, enable: bool):
        value = "1" if enable else "0"
        try:
            run(
                ["sudo", "sysctl", "-w", f"net.ipv4.ip_forward={value}"],
                stdout=PIPE,
                stderr=PIPE,
                check=True,
            )
            log_debug(f"Set ip forwarding to {value}", self.__class__.__qualname__)
        except CalledProcessError as e:
            log_debug(
                f"Exception while setting ip forwarding: {e}",
                self.__class__.__qualname__,
            )

    def create_rule_masq(self, name: str, add: bool) -> list[str]:
        action = "-A"
        if add is False:
            action = "-D"
        return [
            "sudo",
            "iptables",
            "-t",
            "nat",
            action,
            "POSTROUTING",
            "-o",
            name,
            "-j",
            "MASQUERADE",
        ]
