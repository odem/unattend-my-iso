import sys
from datetime import datetime
from unattend_my_iso.common.config import TaskResult, TemplateConfig
from unattend_my_iso.common.logging import log_debug, log_error, log_info, log_warn
from unattend_my_iso.core.reader.reader_config import TaskConfig, get_configs
from unattend_my_iso.core.processing.processor_task_isogen import TaskProcessorIsogen
from unattend_my_iso.core.processing.processor_task_vmrun import TaskProcessorVmRun
from unattend_my_iso.core.processing.processor_task_networking import (
    TaskProcessorNetworking,
)


class UmiTaskProcessor(
    TaskProcessorIsogen, TaskProcessorVmRun, TaskProcessorNetworking
):
    proc_time_start: datetime
    proc_time_stop: datetime
    topic: str

    def __init__(self):
        self.topic = self.__class__.__qualname__
        TaskProcessorIsogen.__init__(self)
        TaskProcessorVmRun.__init__(self)

    def do_process(self):
        taskconfigs = get_configs()
        log_info(f"TaskConfigs : {len(taskconfigs)}",
                 self.topic)
        if len(taskconfigs) > 0:
            for cfg in taskconfigs:
                if isinstance(cfg, TaskConfig):
                    log_info(
                        f"TaskTemplate: {cfg.target.template}",
                        self.topic,
                    )
                    log_info(
                        f"TaskOverlay : {cfg.target.template_overlay}",
                        self.topic,
                    )
                    self._get_addons()
                    self._get_templates(cfg)
                    self._get_overlays(cfg)
                    template = self._get_task_template(cfg)
                    if template is None:
                        log_error(
                            f"TemplateErr : Template is None. Current={template}", self.topic,
                        )
                        sys.exit(2)
                    if template is not None:
                        self.proc_time_start = datetime.now()
                        result = self._process_task(cfg, template)
                        self._process_result(result)
                        self.proc_time_stop = datetime.now()
                        self._log_result(result)
                else:
                    log_error(f"TaskConfig invalid: {taskconfigs}", self.topic)
        else:
            log_error(
                "No Taskconfig available after parsing arguments", self.topic,
            )
            sys.exit(1)

    def _process_task(self, args: TaskConfig, template: TemplateConfig) -> TaskResult:
        log_info(
            f"Template: {args.target.template} ({args.target.template_overlay})",
            self.topic,
        )
        tasktype = args.target.proctype
        if args.run.verbosity >= 4:
            log_debug(f"TaskConfig : {template}", self.topic)
            log_debug(f"TemplateConfig : {args}", self.topic)
        if tasktype == "build_all":
            return self.task_build_all(args)
        if tasktype == "extract":
            return self.task_extract_iso(args)
        if tasktype == "addons":
            return self.task_build_addons(args)
        if tasktype == "irmod":
            return self.task_build_irmod(args)
        if tasktype == "squashmod":
            return self.task_build_squashmod(args)
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
            log_debug(f"Task Success : {result.success}", self.topic)
        else:
            log_error(f"Task Error : Msg:{result.msg}", self.topic)

    def _log_result(self, result: TaskResult):
        dformat = "%Y-%m-%d %H:%M:%S"
        diff = self.proc_time_stop - self.proc_time_start
        start = datetime.strftime(self.proc_time_start, dformat)
        stop = datetime.strftime(self.proc_time_stop, dformat)
        total_seconds = int(diff.total_seconds())
        diff_ms = diff.microseconds / 1000
        diff_text = f"{diff_ms} ms"
        if total_seconds > 0:
            diff_text = f"{total_seconds} s"
        msg = f"{result.success}"
        if result.success is False:
            msg = f"{result.success} -> {result.msg_short}"
        log_info("--- Result -----------------------------------", self.topic)
        log_info(f"Result     : {msg}", self.topic)
        log_info(f"Time Start : {start}", self.topic)
        log_info(f"Time Stop  : {stop}", self.topic)
        log_info(f"Total Time : {diff_text}", self.topic)
        log_info("----------------------------------------------", self.topic)
