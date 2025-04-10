from unattend_my_iso.common.logging import log_debug
from unattend_my_iso.core.net.net_manager_bridges import BridgeManager
from unattend_my_iso.core.net.net_manager_firewall import FirewallManager
from unattend_my_iso.core.net.net_manager_nics import NicManager
from unattend_my_iso.core.vm.hypervisor_base import HypervisorArgs


class UmiNetworkManager(BridgeManager, NicManager, FirewallManager):
    def __init__(self):
        BridgeManager.__init__(self)
        NicManager.__init__(self)
        FirewallManager.__init__(self)

    def net_start(self, args_hv: HypervisorArgs) -> bool:
        self.net_stop(args_hv)
        self.bridges_start(args_hv)
        self.nics_start(args_hv)
        self.nics_assign(args_hv)
        self.fw_start(args_hv)
        return True

    def net_stop(self, args_hv: HypervisorArgs) -> bool:
        self.fw_stop(args_hv)
        self.nics_unassign(args_hv)
        self.nics_stop(args_hv)
        self.bridges_stop(args_hv)
        return True

    def fw_start(self, args_hv: HypervisorArgs) -> bool:
        if args_hv.net_prepare_fw:
            if self.add_masqueradings(args_hv.netbridges) is False:
                return False
        return True

    def fw_stop(self, args_hv: HypervisorArgs) -> bool:
        if args_hv.net_prepare_fw:
            if self.del_masqueradings(args_hv.netbridges) is False:
                return False
        return True

    def bridges_start(self, args_hv: HypervisorArgs) -> bool:
        if args_hv.net_prepare_bridges:
            self.add_bridges(args_hv.netbridges)
        return True

    def bridges_stop(self, args_hv: HypervisorArgs) -> bool:
        if args_hv.net_prepare_bridges:
            self.del_bridges(args_hv.netbridges)
        return True

    def nics_start(self, args_hv: HypervisorArgs) -> bool:
        if args_hv.net_prepare_nics:
            self.del_nics(args_hv.netdevs)
            self.add_nics(args_hv.netdevs)
        return True

    def nics_stop(self, args_hv: HypervisorArgs) -> bool:
        if args_hv.net_prepare_nics:
            self.del_nics(args_hv.netdevs)
        return True

    def nics_assign(self, args_hv: HypervisorArgs) -> bool:
        if args_hv.net_prepare_nics:
            self.unassign_nics(args_hv.netdevs)
            self.assign_nics(args_hv.netdevs)
        return True

    def nics_unassign(self, args_hv: HypervisorArgs) -> bool:
        if args_hv.net_prepare_nics:
            self.unassign_nics(args_hv.netdevs)
        return True
