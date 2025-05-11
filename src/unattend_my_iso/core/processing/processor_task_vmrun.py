import os
from unattend_my_iso.common.config import TaskResult, TaskConfig, TemplateConfig
from unattend_my_iso.common.logging import log_error
from unattend_my_iso.core.processing.processor_base import TaskProcessorBase


class TaskProcessorVmRun(TaskProcessorBase):

    def __init__(self, work_path: str = ""):
        TaskProcessorBase.__init__(self, work_path)

    def task_vm_start(self, args: TaskConfig, template: TemplateConfig) -> TaskResult:
        hyperargs = self.hvrunner.vm_get_args(args, template)
        vmdir = self.files._get_path_vm(args)
        if os.path.exists(vmdir) is False:
            os.makedirs(vmdir)
        recreate = True if args.run.clean_old_vm else False
        if recreate:
            if self.files.rm(vmdir) is False:
                log_error(f"Could not delete vm dir: {vmdir}")
                return self._get_error_result(f"Error on deleting vmdir: {vmdir}")

        if hyperargs is not None:
            if template.iso_type == "windows":
                if self.hvrunner.vm_prepare_tpm(args, hyperargs) is False:
                    return self._get_error_result("Error on swtpm")
            if self.hvrunner.prepare_disk_efi(args) is False:
                return self._get_error_result("Error on prepare disk")
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
