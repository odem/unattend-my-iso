import sys
from unattend_my_iso.common.config import TaskResult
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

    def __init__(self):
        TaskProcessorIsogen.__init__(self)
        TaskProcessorVmRun.__init__(self)

    def do_process(self):
        taskconfigs = get_configs()
        log_debug(f"TaskConfigs : {len(taskconfigs)}", self.__class__.__qualname__)
        if len(taskconfigs) > 0:
            for cfg in taskconfigs:
                if isinstance(cfg, TaskConfig):
                    self._get_addons()
                    self._get_templates(cfg)
                    self._get_overlays(cfg)
                    result = self._process_task(cfg)
                    self._process_result(result)
                else:
                    log_error(
                        f"TaskConfig invalid: {taskconfigs}",
                        self.__class__.__qualname__,
                    )
        else:
            log_error(
                "No Taskconfig available after parsing arguments",
                self.__class__.__qualname__,
            )
            sys.exit(1)

    def _process_task(self, args: TaskConfig) -> TaskResult:
        log_info(
            f"Template: {args.target.template} ({args.target.template_overlay})",
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
        elif tasktype == "exec":
            return self.task_vm_exec(args, template)
        return self._get_error_result("Unknown task")

    def _process_result(self, result: TaskResult):
        if result.success:
            log_debug(f"Task Success : {result.success}", self.__class__.__qualname__)
        else:
            log_debug(f"Task Error : Msg:{result.msg}", self.__class__.__qualname__)
