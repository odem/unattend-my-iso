from unattend_my_iso.core.net.net_manager_bridges import BridgeManager
from unattend_my_iso.core.net.net_manager_nics import NicManager
from unattend_my_iso.core.vm.hypervisor_base import HypervisorArgs
from unattend_my_iso.common.logging import log_info


class UmiNetworkManager(BridgeManager, NicManager):
    def __init__(self):
        BridgeManager.__init__(self)
        NicManager.__init__(self)

    def net_start(self, args_hv: HypervisorArgs) -> bool:
        if args_hv.net_prepare_nics:
            self.unassign_nics(args_hv.netdevs)
            self.del_nics(args_hv.netdevs)
        if args_hv.net_prepare_bridges:
            self.del_bridges(args_hv.netdevs)
            self.add_bridges(args_hv.netdevs)
        if args_hv.net_prepare_nics:
            self.create_nics(args_hv.netdevs)
            self.assign_nics(args_hv.netdevs)
        return True

    def net_stop(self, args_hv: HypervisorArgs) -> bool:
        if args_hv.net_prepare_nics:
            self.unassign_nics(args_hv.netdevs)
            self.del_nics(args_hv.netdevs)
        if args_hv.net_prepare_bridges:
            self.del_bridges(args_hv.netdevs)
        return True
