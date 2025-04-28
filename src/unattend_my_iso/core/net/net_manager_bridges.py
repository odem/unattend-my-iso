from unattend_my_iso.core.subprocess.caller import (
    run,
    CalledProcessError,
    PIPE,
)
from unattend_my_iso.common.logging import log_debug, log_error


class BridgeManager:
    def __init__(self):
        pass

    def prepare_bridge(self, name: str, ip: str, mask: str) -> bool:
        if self.has_bridge(name) is False:
            if self.add_bridge(name, ip, mask) is False:
                log_error("Bridge not created", self.__class__.__qualname__)
                return False
            log_error(f"Bridge {name} prepared", self.__class__.__qualname__)
        return True

    def has_bridge(self, name: str) -> bool:
        rmcmd = ["sudo", "ip", "link", "show", name]
        try:
            run(rmcmd, capture_output=True, text=True, check=True)
        except CalledProcessError:
            return False
        return True

    def add_bridge(self, name: str, ip: str, mask: str) -> bool:
        try:
            run(["sudo", "ip", "link", "add", name, "type", "bridge"], check=True)
            run(["sudo", "ip", "link", "set", name, "up"], check=True)
            run(["sudo", "ip", "addr", "add", f"{ip}/{mask}", "dev", name], check=True)
            log_debug(f"Bridge {name} created", self.__class__.__qualname__)
        except CalledProcessError as e:
            log_error(
                f"Error creating bridge {name}: {e}",
                self.__class__.__qualname__,
            )
            return False
        return True

    def del_bridge(self, name: str) -> bool:
        try:
            run(["sudo", "ip", "link", "delete", name], check=True)
            log_debug(f"Bridge {name} deleted", self.__class__.__qualname__)
        except CalledProcessError as e:
            log_error(
                f"Error deleting bridge {name}: {e}",
                self.__class__.__qualname__,
            )
            return False
        return True

    def del_bridges(self, brlists: list[list[str]]) -> bool:
        for devlist in brlists:
            if len(devlist) == 4:
                bridge = devlist[0]
                if self.has_bridge(bridge):
                    if self.del_bridge(bridge) is False:
                        return False
        return True

    def add_bridges(self, brlists: list[list[str]]) -> bool:
        for brlist in brlists:
            if len(brlist) == 4:
                bridge = brlist[0]
                ip = brlist[1]
                mask = brlist[2]
                if self.has_bridge(bridge) is False:
                    if self.add_bridge(bridge, ip, mask) is False:
                        return False
        return True

    def has_nic(self, name: str):
        try:
            result = run(
                ["ip", "link", "show", name],
                stdout=PIPE,
                stderr=PIPE,
            )
            if result.returncode == 0:
                return True
            else:
                return False
        except CalledProcessError as e:
            log_error(
                f"Error checking interface {name}: {e}",
                self.__class__.__qualname__,
            )
            return False

    def add_nic(self, name: str):
        try:
            run(["sudo", "ip", "tuntap", "add", "dev", name, "mode", "tap"], check=True)
            run(["sudo", "ip", "link", "set", "dev", name, "up"], check=True)
            log_debug(f"Nic {name} created", self.__class__.__qualname__)
        except CalledProcessError as e:
            log_error(f"Error creating {name}: {e}")
            return False
        return True

    def del_nic(self, name: str):
        try:
            run(["sudo", "ip", "tuntap", "del", "dev", name, "mode", "tap"], check=True)
            log_debug(f"Nic {name} deleted", self.__class__.__qualname__)
        except CalledProcessError as e:
            log_error(
                f"Error removing {name}: {e}",
                self.__class__.__qualname__,
            )
            return False
        return True

    def add_nics(self, devlists: list[list[str]]):
        for devlist in devlists:
            if len(devlist) == 2:
                name = devlist[0]
                self.add_nic(name)
        return True

    def del_nics(self, devlists: list[list[str]]):
        for devlist in devlists:
            if len(devlist) > 0:
                name = devlist[0]
                if self.has_nic(name):
                    self.del_nic(name)
        return True

    def assign_nics(self, devlists: list[list[str]]):
        for devlist in devlists:
            if len(devlist) == 2:
                name = devlist[0]
                bridge = devlist[1]
                if self.assign_nic(name, bridge) is False:
                    return False
        return True

    def unassign_nics(self, devlists: list[list[str]]):
        for devlist in devlists:
            if len(devlist) == 2:
                name = devlist[0]
                bridge = devlist[1]
                if self.has_nic(name):
                    self.unassign_nic(name, bridge)
        return True

    def assign_nic(self, dev: str, bridge: str):
        try:
            run(["sudo", "ip", "link", "set", dev, "master", bridge], check=True)
            log_debug(
                f"{dev} assigned to {bridge}",
                self.__class__.__qualname__,
            )
        except CalledProcessError as e:
            log_error(
                f"Error assigning {dev} to {bridge}: {e}",
                self.__class__.__qualname__,
            )
            return False
        return True

    def unassign_nic(self, dev: str, bridge: str) -> bool:
        try:
            run(["sudo", "ip", "link", "set", dev, "nomaster"], check=True)
            log_debug(
                f"{dev} unassigned from {bridge}",
                self.__class__.__qualname__,
            )
        except CalledProcessError as e:
            log_error(
                f"Error unassigning {dev} from {bridge}: {e}",
                self.__class__.__qualname__,
            )
            return False
        return True
