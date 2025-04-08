from unattend_my_iso.common.common import TaskResult
from unattend_my_iso.common.config import TaskConfig, TemplateConfig
from unattend_my_iso.core.processing.processor_base import TaskProcessorBase


class TaskProcessorVmRun(TaskProcessorBase):

    def __init__(self, work_path: str = ""):
        TaskProcessorBase.__init__(self, work_path)

    def task_vm_start(self, args: TaskConfig, template: TemplateConfig) -> TaskResult:
        hyperargs = self.hvrunner.vm_get_args(args, template)
        vmdir = self.files._get_path_vm(args)
        socketdir = f"{vmdir}/swtpm"
        if hyperargs is not None:
            if template.iso_type == "windows":
                if self.hvrunner.vm_prepare_tpm(socketdir, template) is False:
                    return self._get_error_result("Error on swtpm")
            if self.hvrunner.vm_prepare_disks(args, hyperargs) is False:
                return self._get_error_result("Error on prepare disk")
            if self.hvrunner.vm_run(args, hyperargs) is False:
                return self._get_error_result("Error on VMRUN")
        return self._get_success_result()

    def task_vm_stop(self, args: TaskConfig, template: TemplateConfig) -> TaskResult:
        hyperargs = self.hvrunner.vm_get_args(args, template)
        if hyperargs is not None:
            if self.hvrunner.vm_stop(args, hyperargs) is False:
                return self._get_error_result("Error on VMSTOP")
        return self._get_success_result()
