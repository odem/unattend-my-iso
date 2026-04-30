from dataclasses import dataclass
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


@dataclass
class TimingsProc():
    time_proc_start: datetime = datetime.now()
    time_proc_stop: datetime = datetime.now()
    time_config_start: datetime = datetime.now()
    time_config_stop: datetime = datetime.now()


class UmiTaskProcessor(
    TaskProcessorIsogen, TaskProcessorVmRun, TaskProcessorNetworking
):
    topic: str
    timings: TimingsProc = TimingsProc()

    def __init__(self):
        self.topic = self.__class__.__qualname__
        TaskProcessorIsogen.__init__(self)
        TaskProcessorVmRun.__init__(self)

    def do_process(self):
        taskconfigs = get_configs()
        log_info(f"TaskConfigs : {len(taskconfigs)}", self.topic)
        if len(taskconfigs) > 0:
            for cfg in taskconfigs:
                if isinstance(cfg, TaskConfig):
                    self.timings.time_config_start = datetime.now()
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
                    self.timings.time_config_stop = datetime.now()
                    if template is not None:
                        self.timings.time_proc_start = datetime.now()
                        result = self._process_task(cfg, template)
                        self._process_result(result)
                        self.timings.time_proc_stop = datetime.now()
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
        dproc = self.timings.time_proc_stop - self.timings.time_proc_start
        dconf = self.timings.time_config_stop - self.timings.time_config_start
        dfull = self.timings.time_proc_stop - self.timings.time_config_start
        dconf_s = (dconf.total_seconds() + dconf.microseconds / 1000000)
        dproc_s = (dproc.total_seconds() + dproc.microseconds / 1000000)
        dfull_s = (dfull.total_seconds() + dfull.microseconds / 1000000)
        t = self.topic
        log_info("--- Result -----------------------------------", t)
        log_info(f"Ret  : {result.success}{result.msg_short}", t)
        log_info(f"Conf : {dconf_s * 1000:10.1f} ms -> {dconf_s:10.1f} s ", t)
        log_info(f"Proc : {dproc_s * 1000:10.1f} ms -> {dproc_s:10.1f} s ", t)
        log_info(f"Full : {dfull_s * 1000:10.1f} ms -> {dfull_s:10.1f} s ", t)
        log_info("----------------------------------------------", t)
