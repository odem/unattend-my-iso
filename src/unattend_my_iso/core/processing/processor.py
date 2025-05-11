from unattend_my_iso.common.config import TaskResult
from unattend_my_iso.common.const import GLOBAL_WORKPATHS
from unattend_my_iso.common.logging import log_debug, log_error, log_info
from unattend_my_iso.core.reader.reader_config import TaskConfig, get_configs
from unattend_my_iso.core.processing.processor_task_isogen import TaskProcessorIsogen
from unattend_my_iso.core.processing.processor_task_vmrun import TaskProcessorVmRun
from unattend_my_iso.core.processing.processor_task_networking import (
    TaskProcessorNetworking,
)


class UmiTaskProcessor(
    TaskProcessorIsogen, TaskProcessorVmRun, TaskProcessorNetworking
):

    def __init__(self, work_path: str = ""):
        TaskProcessorIsogen.__init__(self, work_path)
        TaskProcessorVmRun.__init__(self, work_path)
        if work_path == "":
            log_debug(
                f"Global work_path search space: {GLOBAL_WORKPATHS}",
                self.__class__.__qualname__,
            )
            log_info(
                f"Using searched work_path: {self.work_path}",
                self.__class__.__qualname__,
            )
        else:
            log_info(
                f"Using supplied work_path: {self.work_path}",
                self.__class__.__qualname__,
            )

    def do_process(self):
        taskconfigs = get_configs(self.work_path)
        log_debug(f"TaskConfigs : {len(taskconfigs)}", self.__class__.__qualname__)
        for cfg in taskconfigs:
            if isinstance(cfg, TaskConfig):
                result = self._process_task(cfg)
                self._process_result(result)
            else:
                log_error(
                    f"TaskConfig invalid: {taskconfigs}", self.__class__.__qualname__
                )

    def _process_task(self, args: TaskConfig) -> TaskResult:
        log_debug(
            f"Task : {args.target.template} ({args.target.template_overlay})",
            self.__class__.__qualname__,
        )
        tasktype = args.target.proctype
        template = self._get_task_template(args)
        if template is None:
            return self._get_error_result("No template")
        if args.run.verbosity >= 4:
            log_debug(f"TaskConfig : {template}", self.__class__.__qualname__)
            log_debug(f"TemplateConfig : {args}", self.__class__.__qualname__)
        if tasktype == "build_all":
            return self.task_build_all(args)
        if tasktype == "extract":
            return self.task_extract_iso(args)
        if tasktype == "addons":
            return self.task_build_addons(args)
        if tasktype == "irmod":
            return self.task_build_irmod(args)
        if tasktype == "iso":
            return self.task_build_iso(args)
        elif tasktype == "net_start":
            return self.task_vm_netstart(args, template)
        elif tasktype == "net_stop":
            return self.task_vm_netstop(args, template)
        elif tasktype == "vm_start":
            return self.task_vm_start(args, template)
        elif tasktype == "vm_stop":
            return self.task_vm_stop(args, template)
        return self._get_error_result("Unknown task")

    def _process_result(self, result: TaskResult):
        if result.success:
            log_debug(f"Task Success : {result.success}", self.__class__.__qualname__)
        else:
            log_debug(f"Task Error : Msg:{result.msg}", self.__class__.__qualname__)
