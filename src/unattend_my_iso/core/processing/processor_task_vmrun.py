from unattend_my_iso.common.common import TaskResult
from unattend_my_iso.common.config import TaskConfig
from unattend_my_iso.core.processing.processor_base import TaskProcessorBase


class TaskProcessorVmRun(TaskProcessorBase):

    def __init__(self, work_path: str = ""):
        TaskProcessorBase.__init__(self, work_path)

    def task_vm_run(self, args: TaskConfig) -> TaskResult:
        hyperargs = self.hvrunner.vm_get_args(args)
        if hyperargs is not None:
            if self.hvrunner.vm_prepare_disks(args, hyperargs):
                self.hvrunner.vm_run(args, hyperargs)
        return self._get_error_result("")
