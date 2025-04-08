from unattend_my_iso.common.common import TaskResult
from unattend_my_iso.common.config import TaskConfig, TemplateConfig
from unattend_my_iso.core.processing.processor_base import TaskProcessorBase


class TaskProcessorNetworking(TaskProcessorBase):

    def __init__(self, work_path: str = ""):
        TaskProcessorBase.__init__(self, work_path)

    def task_vm_netstart(
        self, args: TaskConfig, template: TemplateConfig
    ) -> TaskResult:
        hyperargs = self.hvrunner.vm_get_args(args, template)
        if self.netman.net_start(hyperargs) is False:
            return self._get_error_result("Error on VMRUN")
        return self._get_success_result()

    def task_vm_netstop(self, args: TaskConfig, template: TemplateConfig) -> TaskResult:
        hyperargs = self.hvrunner.vm_get_args(args, template)
        if self.netman.net_stop(hyperargs) is False:
            return self._get_error_result("Error on VMRUN")
        return self._get_success_result()
