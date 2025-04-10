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
        if name == "":
            log_error(
                f"The uplink device name was empty: {name}", self.__class__.__qualname__
            )
            return False
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

    def get_default_route_interfaces(self) -> list[str]:
        try:
            output = subprocess.check_output(
                ["ip", "route", "show", "default"], text=True
            )
            interfaces = []
            for line in output.strip().splitlines():
                parts = line.split()
                if "dev" in parts:
                    dev_index = parts.index("dev") + 1
                    if dev_index < len(parts):
                        interfaces.append(parts[dev_index])
            return interfaces

        except subprocess.CalledProcessError as e:
            print(f"Error running ip route: {e}")
            return []

    def set_ip_forwarding(self, enable: bool):
        value = "1" if enable else "0"
        try:
            subprocess.run(
                ["sudo", "sysctl", "-w", f"net.ipv4.ip_forward={value}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            log_debug(f"Set ip forwarding to {value}", self.__class__.__qualname__)
        except subprocess.CalledProcessError as e:
            log_debug(
                f"Exception while setting ip forwarding: {e}",
                self.__class__.__qualname__,
            )
