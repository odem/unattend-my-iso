import subprocess
from unattend_my_iso.common.logging import log_debug, log_error


class NicManager:
    def __init__(self):
        pass

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
            log_error(f"NicManager   : Error checking interface {name}: {e}")
            return False

    def create_nic(self, name: str):
        try:
            subprocess.run(
                ["sudo", "ip", "tuntap", "add", "dev", name, "mode", "tap"], check=True
            )
            subprocess.run(["sudo", "ip", "link", "set", "dev", name, "up"], check=True)
        except subprocess.CalledProcessError as e:
            log_error(f"NicManager   : Error creating {name}: {e}")
            return False
        return True

    def create_nics(self, devlists: list[list[str]]):
        log_debug("NicManager   : Deleting all nics")
        for devlist in devlists:
            name = devlist[0]
            self.create_nic(name)
        return True

    def del_nics(self, devlists: list[list[str]]):
        log_debug("NicManager   : Deleting all nics")
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
            log_error(f"NicManager   : Error removing {name}: {e}")
            return False
        return True

    def assign_nics(self, devlists: list[list[str]]):
        log_debug("NicManager   : Assigning all nics to bridges")
        for devlist in devlists:
            name = devlist[0]
            bridge = devlist[1]
            if self.assign_nic(name, bridge) is False:
                return False
        return True

    def unassign_nics(self, devlists: list[list[str]]):
        log_debug("NicManager   : Unassigning all nics from bridges")
        for devlist in devlists:
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
            log_debug(f"NicManager   : {dev} assigned to {bridge}")
        except subprocess.CalledProcessError as e:
            log_error(f"NicManager   : Error assigning {dev} to {bridge}: {e}")
            return False
        return True

    def unassign_nic(self, dev: str, bridge: str) -> bool:
        try:
            subprocess.run(["sudo", "ip", "link", "set", dev, "nomaster"], check=True)
            log_debug(f"NicManager   : {dev} unassigned from {bridge}")
        except subprocess.CalledProcessError as e:
            log_error(f"NicManager   : Error unassigning {dev} from {bridge}: {e}")
            return False
        return True
