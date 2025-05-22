from unattend_my_iso.common.config import TaskResult, TaskConfig, TemplateConfig
from unattend_my_iso.core.processing.processor_base import TaskProcessorBase


class TaskProcessorNetworking(TaskProcessorBase):

    def __init__(self):
        TaskProcessorBase.__init__(self)

    def task_vm_netstart(
        self, args: TaskConfig, template: TemplateConfig
    ) -> TaskResult:
        hyperargs = self.hvrunner.vm_get_args(args, template)
        if self.netman.net_start(hyperargs) is False:
            return self._get_error_result("Error on net_start")
        return self._get_success_result()

    def task_vm_netstop(self, args: TaskConfig, template: TemplateConfig) -> TaskResult:
        hyperargs = self.hvrunner.vm_get_args(args, template)
        if self.netman.net_stop(hyperargs) is False:
            return self._get_error_result("Error on net_stop")
        return self._get_success_result()
