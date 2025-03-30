from unattend_my_iso.common.common import TaskResult
from unattend_my_iso.common.config import TaskConfig, get_config
from unattend_my_iso.core.processing.processor_task_isogen import TaskProcessorIsogen
from unattend_my_iso.core.processing.processor_task_vmrun import TaskProcessorVmRun
from unattend_my_iso.common.logging import log_debug, log_error


class TaskProcessor(TaskProcessorIsogen, TaskProcessorVmRun):

    def __init__(self, work_path: str = ""):
        TaskProcessorIsogen.__init__(self, work_path)
        TaskProcessorVmRun.__init__(self, work_path)

    def do_process(self):
        taskconfig = get_config(self.work_path)
        if isinstance(taskconfig, TaskConfig):
            result = self._process_task(taskconfig)
            self._process_result(result)
        else:
            log_error(f"TaskConfig invalid: {taskconfig}")

    def _process_task(self, args: TaskConfig) -> TaskResult:
        tasktype = args.target.proctype
        if tasktype == "all":
            return self.task_build_all(args)
        if tasktype == "extract":
            return self.task_extract_iso(args)
        if tasktype == "addons":
            return self.task_build_addons(args)
        if tasktype == "irmod":
            return self.task_build_irmod(args)
        if tasktype == "iso":
            return self.task_build_iso(args)
        elif tasktype == "run":
            template = self._get_task_template(args)
            if template is None:
                return self._get_error_result("No template")
            return self.task_vm_run(args, template)
        return self._get_error_result("Unknown task")

    def _process_result(self, result: TaskResult):
        log_debug(f"Success: {result.success}, Msg:{result.msg}")
