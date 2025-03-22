from unattend_my_iso.common.common import TaskResult
from unattend_my_iso.common.config import TaskConfig, TemplateConfig
from unattend_my_iso.common.logging import log_debug
from unattend_my_iso.core.processing.processor_base import TaskProcessorBase


class TaskProcessorVmRun(TaskProcessorBase):

    def __init__(self, work_path: str = ""):
        TaskProcessorBase.__init__(self, work_path)

    def task_vm_run(self, args: TaskConfig, template: TemplateConfig) -> TaskResult:
        hyperargs = self.hvrunner.vm_get_args(args, template)
        if hyperargs is not None:
            if self.hvrunner.vm_prepare_disks(args, hyperargs) is False:
                return self._get_error_result("Error on prepare disk")
            vmdir = self.files._get_path_vm(args)
            socketdir = f"{vmdir}/swtpm"
            log_debug(f"SOCKETDIR: {socketdir}")
            if self.hvrunner.vm_prepare_tpm(socketdir) is False:
                return self._get_error_result("Error on swtpm")
            if self.hvrunner.vm_run(args, hyperargs) is False:
                return self._get_error_result("Error on VMRUN")
        return self._get_success_result()
