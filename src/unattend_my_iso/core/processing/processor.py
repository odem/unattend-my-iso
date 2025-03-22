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
        tasktype = "vmbuild_all"
        if len(arguments) > 0:
            tasktype = arguments[0]
        if tasktype == "vmbuild_all":
            return self.task_build_all(args, user)
        if tasktype == "vmbuild_intermediate":
            return self.task_build_intermediate(args)
        if tasktype == "vmbuild_addons":
            return self.task_build_addons(args)
        if tasktype == "vmbuild_irmod":
            return self.task_build_irmod(args)
        if tasktype == "vmbuild_iso":
            return self.task_build_iso(args, user)
        elif tasktype == "vmrun":
            template = self._get_task_template(args)
            if template is None:
                return self._get_error_result("No template")
            return self.task_vm_run(args, template)
        return self._get_error_result("Unknown task")

    def _process_result(self, result: TaskResult):
        log_debug(f"Success: {result.success}, Msg:{result.msg}")
