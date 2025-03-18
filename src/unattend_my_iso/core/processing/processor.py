from unattend_my_iso.common.common import TaskResult
from unattend_my_iso.common.config import TaskConfig, get_cfg_task
from unattend_my_iso.core.processing.processor_task_isogen import TaskProcessorIsogen
from unattend_my_iso.core.processing.processor_task_vmrun import TaskProcessorVmRun
from unattend_my_iso.common.logging import log_debug


class TaskProcessor(TaskProcessorIsogen, TaskProcessorVmRun):

    def __init__(self, work_path: str = ""):
        TaskProcessorIsogen.__init__(self, work_path)
        TaskProcessorVmRun.__init__(self, work_path)

    def do_process(self, script_name: str = "", arguments: list = []):
        taskconfig = get_cfg_task(self.work_path)
        self._print_args(taskconfig)
        result = self._process_task(taskconfig, script_name, arguments)
        self._process_result(result)

    def _process_task(
        self, args: TaskConfig, script_name: str = "", arguments: list = []
    ) -> TaskResult:
        user = "jb"
        tasktype = "vmbuild"
        if len(arguments) > 0:
            tasktype = arguments[0]
        if tasktype == "vmbuild":
            return self.task_build_iso(args, user)
        elif tasktype == "vmrun":
            return self.task_vm_run(args)
        return self._get_error_result("Unknown task")

    def _process_result(self, result: TaskResult):
        log_debug(f"Result: {result.success}")
