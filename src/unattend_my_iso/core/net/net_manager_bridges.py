import subprocess
from unattend_my_iso.common.logging import log_debug, log_error


class BridgeManager:
    def __init__(self):
        pass

    def prepare_bridge(self, name: str) -> bool:
        if self.has_bridge(name) is False:
            if self.add_bridge(name) is False:
                log_error("Bridge not created", self.__class__.__qualname__)
                return False
            log_error(f"Bridge {name} prepared", self.__class__.__qualname__)
        return True

    def has_bridge(self, name: str) -> bool:
        rmcmd = ["sudo", "ip", "link", "show", name]
        try:
            subprocess.run(rmcmd, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError:
            return False
        return True

    def add_bridge(self, name: str) -> bool:
        try:
            subprocess.run(
                ["sudo", "ip", "link", "add", name, "type", "bridge"], check=True
            )
            subprocess.run(["sudo", "ip", "link", "set", name, "up"], check=True)
            log_debug(f"Bridge {name} created", self.__class__.__qualname__)
        except subprocess.CalledProcessError as e:
            log_error(
                f"Error creating bridge {name}: {e}",
                self.__class__.__qualname__,
            )
            return False
        return True

    def del_bridge(self, name: str) -> bool:
        try:
            subprocess.run(["sudo", "ip", "link", "delete", name], check=True)
            log_debug(f"Bridge {name} deleted", self.__class__.__qualname__)
        except subprocess.CalledProcessError as e:
            log_error(
                f"Error deleting bridge {name}: {e}",
                self.__class__.__qualname__,
            )
            return False
        return True

    def del_bridges(self, devlists: list[list[str]]) -> bool:
        log_debug("Deleting all bridges", self.__class__.__qualname__)
        for devlist in devlists:
            if len(devlist) == 2:
                bridge = devlist[1]
                if self.has_bridge(bridge):
                    if self.del_bridge(bridge) is False:
                        return False
        return True

    def add_bridges(self, devlists: list[list[str]]) -> bool:
        log_debug("Adding all bridges", self.__class__.__qualname__)
        for devlist in devlists:
            if len(devlist) == 2:
                bridge = devlist[1]
                if self.has_bridge(bridge) is False:
                    if self.add_bridge(bridge) is False:
                        return False
        return True

    def has_nic(self, name: str):
        try:
            result = subprocess.run(
                ["ip", "link", "show", name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            if result.returncode == 0:
                return True
            else:
                return False
        except subprocess.CalledProcessError as e:
            log_error(
                f"Error checking interface {name}: {e}",
                self.__class__.__qualname__,
            )
            return False

    def create_nic(self, name: str):
        try:
            subprocess.run(
                ["sudo", "ip", "tuntap", "add", "dev", name, "mode", "tap"], check=True
            )
            subprocess.run(["sudo", "ip", "link", "set", "dev", name, "up"], check=True)
        except subprocess.CalledProcessError as e:
            log_error(f"Error creating {name}: {e}")
            return False
        return True

    def create_nics(self, devlists: list[list[str]]):
        log_debug("Deleting all nics", self.__class__.__qualname__)
        for devlist in devlists:
            if len(devlist) == 2:
                name = devlist[0]
                self.create_nic(name)
        return True

    def del_nics(self, devlists: list[list[str]]):
        log_debug("Deleting all nics", self.__class__.__qualname__)
        for devlist in devlists:
            name = devlist[0]
            if self.has_nic(name):
                self.del_nic(name)
        return True

    def del_nic(self, name: str):
        try:
            subprocess.run(
                ["sudo", "ip", "tuntap", "del", "dev", name, "mode", "tap"], check=True
            )
        except subprocess.CalledProcessError as e:
            log_error(
                f"Error removing {name}: {e}",
                self.__class__.__qualname__,
            )
            return False
        return True

    def assign_nics(self, devlists: list[list[str]]):
        log_debug("Assigning all nics to bridges", self.__class__.__qualname__)
        for devlist in devlists:
            if len(devlist) == 2:
                name = devlist[0]
                bridge = devlist[1]
                if self.assign_nic(name, bridge) is False:
                    return False
        return True

    def unassign_nics(self, devlists: list[list[str]]):
        log_debug(
            "Unassigning all nics from bridges",
            self.__class__.__qualname__,
        )
        for devlist in devlists:
            if len(devlist) == 2:
                name = devlist[0]
                bridge = devlist[1]
                if self.has_nic(name):
                    self.unassign_nic(name, bridge)
        return True

    def assign_nic(self, dev: str, bridge: str):
        try:
            subprocess.run(
                ["sudo", "ip", "link", "set", dev, "master", bridge], check=True
            )
            log_debug(
                f"{dev} assigned to {bridge}",
                self.__class__.__qualname__,
            )
        except subprocess.CalledProcessError as e:
            log_error(
                f"Error assigning {dev} to {bridge}: {e}",
                self.__class__.__qualname__,
            )
            return False
        return True

    def unassign_nic(self, dev: str, bridge: str) -> bool:
        try:
            subprocess.run(["sudo", "ip", "link", "set", dev, "nomaster"], check=True)
            log_debug(
                f"{dev} unassigned from {bridge}",
                self.__class__.__qualname__,
            )
        except subprocess.CalledProcessError as e:
            log_error(
                f"Error unassigning {dev} from {bridge}: {e}",
                self.__class__.__qualname__,
            )
            return False
        return True
