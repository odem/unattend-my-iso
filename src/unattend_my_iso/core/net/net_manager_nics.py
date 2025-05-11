from unattend_my_iso.core.subprocess.caller import run, CalledProcessError, PIPE
from unattend_my_iso.common.logging import log_debug, log_error


class NicManager:
    def __init__(self):
        pass

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
                f"Error checking interface {name}: {e}", self.__class__.__qualname__
            )
            return False

    def create_nic(self, name: str):
        try:
            run(["sudo", "ip", "tuntap", "add", "dev", name, "mode", "tap"], check=True)
            run(["sudo", "ip", "link", "set", "dev", name, "up"], check=True)
        except CalledProcessError as e:
            log_error(f"Error creating {name}: {e}", self.__class__.__qualname__)
            return False
        return True

    def create_nics(self, devlists: list[list[str]]):
        for devlist in devlists:
            name = devlist[0]
            self.create_nic(name)
        return True

    def del_nics(self, devlists: list[list[str]]):
        for devlist in devlists:
            name = devlist[0]
            if self.has_nic(name):
                self.del_nic(name)
        return True

    def del_nic(self, name: str):
        try:
            run(["sudo", "ip", "tuntap", "del", "dev", name, "mode", "tap"], check=True)
        except CalledProcessError as e:
            log_error(f"Error removing {name}: {e}", self.__class__.__qualname__)
            return False
        return True

    def assign_nics(self, devlists: list[list[str]]):
        for devlist in devlists:
            name = devlist[0]
            bridge = devlist[1]
            if self.assign_nic(name, bridge) is False:
                return False
        return True

    def unassign_nics(self, devlists: list[list[str]]):
        for devlist in devlists:
            name = devlist[0]
            bridge = devlist[1]
            if self.has_nic(name):
                self.unassign_nic(name, bridge)
        return True

    def assign_nic(self, dev: str, bridge: str):
        try:
            run(["sudo", "ip", "link", "set", dev, "master", bridge], check=True)
            log_debug(f"{dev} assigned to {bridge}", self.__class__.__qualname__)
        except CalledProcessError as e:
            log_error(
                f"Error assigning {dev} to {bridge}: {e}", self.__class__.__qualname__
            )
            return False
        return True

    def unassign_nic(self, dev: str, bridge: str) -> bool:
        try:
            run(["sudo", "ip", "link", "set", dev, "nomaster"], check=True)
            log_debug(f"{dev} unassigned from {bridge}", self.__class__.__qualname__)
        except CalledProcessError as e:
            log_error(
                f"Error unassigning {dev} from {bridge}: {e}",
                self.__class__.__qualname__,
            )
            return False
        return True
