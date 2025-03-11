import os
from unattend_my_iso.helpers.config import IsoTemplate, TaskConfig, TaskResult
from unattend_my_iso.helpers.files import copy_file, copy_folder
from unattend_my_iso.helpers.geniso import generate_md5sum_and_create_iso
from unattend_my_iso.helpers.irmod import create_irmod
from unattend_my_iso.helpers.kvm import HypervisorArgs, run_vm
from unattend_my_iso.helpers.logging import log_debug, log_error
from unattend_my_iso.process.processor_base import TaskProcessorBase


class TaskProcessor(TaskProcessorBase):

    def do_process(self, script_name: str = "", arguments: list = []):
        self._print_args(self.taskconfig)
        result = self._process_task(self.taskconfig, script_name, arguments)
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

    def task_vm_run(self, args: TaskConfig) -> TaskResult:
        isopath = self.taskconfig.sys.iso_path
        isoname = args.target.template
        dst = f"{isopath}/umi_{isoname}.iso"
        vmdir = f"{args.sys.vm_path}/{args.target.template}"
        os.makedirs(vmdir, exist_ok=True)
        hyperargs = HypervisorArgs(
            args.target.template,
            True,
            "",
            [f"{vmdir}/disk1.qcow2"],
            ["nat"],
            [(2222, 22)],
            4,
            4096,
        )
        run_vm(args, hyperargs)
        return self._get_error_result("")

    def task_build_iso(self, args: TaskConfig, user: str) -> TaskResult:
        name = args.target.template
        if self._ensure_task_template(args) is False:
            return self._get_error_result("No template")

        template = self.templates[name]
        if template is None or self._ensure_task_iso(template) is False:
            return self._get_error_result("No ISO")

        if self._extract_iso_contents(args, template, user) is False:
            return self._get_error_result("Not extracted")

        if self._copy_preseed(args, template) is False:
            return self._get_error_result("Preseed not copied")

        if self._copy_addons(args, template, user) is False:
            return self._get_error_result("Addons not copied")

        if self._create_irmod(args) is False:
            return self._get_error_result("irmod not created")

        if self._generate_iso(args, template, user) is False:
            return self._get_error_result("iso not generated")

        return self._get_success_result()

    def _generate_iso(self, args: TaskConfig, template: IsoTemplate, user: str) -> bool:
        isopath = self.taskconfig.sys.iso_path
        isoname = args.target.template
        interpath = self.taskconfig.sys.intermediate_path
        intername = args.target.template
        fullinter = f"{interpath}/{intername}"
        dst = f"{isopath}/umi_{isoname}"
        created = generate_md5sum_and_create_iso(
            fullinter, template.iso_name, dst, user
        )
        if created is True:
            log_debug(f"Created ISO   : {dst}")
        else:
            log_error("Error during ISO create")
        return created

    def _create_irmod(self, args: TaskConfig) -> bool:
        templatepath = self.taskconfig.sys.template_path
        templatename = args.target.template
        interpath = self.taskconfig.sys.intermediate_path
        intername = args.target.template
        src = f"{templatepath}/{templatename}"
        try:
            if (
                create_irmod(
                    f"{interpath}/{intername}/irmod",
                    f"{interpath}/{intername}",
                    src,
                )
                is False
            ):
                return False
            log_debug(f"Created irmod : {interpath}/{intername}/irmod")
        except Exception as exe:
            print(f"Exception: {exe}")
        return True

    def _copy_addons(self, args: TaskConfig, template: IsoTemplate, user: str) -> bool:
        templatepath = self.taskconfig.sys.template_path
        templatename = args.target.template
        interpath = self.taskconfig.sys.intermediate_path
        intername = args.target.template
        src = f"{templatepath}/{templatename}"
        dst = f"{interpath}/{intername}/umi"
        dstgrub = f"{interpath}/{intername}/boot/grub"
        srcgrub = f"{src}/{template.path_grub}"
        if args.addons.addon_grubmenu:
            os.makedirs(dstgrub, exist_ok=True)
            if copy_folder(f"{srcgrub}/theme", dstgrub, user) is False:
                return False
            if copy_file(f"{srcgrub}/grub.cfg", dstgrub) is False:
                return False
            log_debug("Copied addon  : Grub")
        if args.addons.addon_ssh:
            if copy_folder(f"{src}/{template.path_ssh}", dst, user) is False:
                return False
            log_debug("Copied addon  : Ssh")
        if args.addons.addon_postinstall:
            postfolder = f"{src}/{template.path_postinstall}"
            if copy_folder(postfolder, dst, user) is False:
                return False
            log_debug("Copied addon  : Postinstall")
        return True

    def _copy_preseed(self, args: TaskConfig, template: IsoTemplate) -> bool:
        templatepath = self.taskconfig.sys.template_path
        templatename = args.target.template
        interpath = self.taskconfig.sys.intermediate_path
        intername = args.target.template
        fullpreseed = f"{templatepath}/{templatename}/{template.preseed_file}"
        fullinter = f"{interpath}/{intername}"
        if copy_file(fullpreseed, fullinter):
            log_debug(f"Copied preseed: {fullpreseed}")
            return True
        return False

    def _extract_iso_contents(
        self, args: TaskConfig, template: IsoTemplate, user: str
    ) -> bool:
        interpath = self.taskconfig.sys.intermediate_path
        isopath = self.taskconfig.sys.iso_path
        isoname = template.iso_name
        fulliso = f"{isopath}/{isoname}"
        fulldst = f"{args.sys.mnt_path}/{args.target.template}"
        self._unmount_folder(fulldst)
        if self._mount_folder(fulliso, args.target.template, args.sys.mnt_path):
            copied = copy_folder(fulldst, interpath, user)
            self._unmount_folder(fulldst)
            if copied:
                log_debug(f"Copied ISO    : {isoname}")
                return True
        return False

    def _ensure_task_template(self, args: TaskConfig) -> bool:
        name = args.target.template
        if name in self.templates.keys():
            return True
        return False

    def _ensure_task_iso(self, template: IsoTemplate) -> bool:
        isopath = self.taskconfig.sys.iso_path
        isoname = template.iso_name
        fullname = f"{isopath}/{isoname}"
        if self.exists(fullname):
            pass
        else:
            self._download_file(template)
        return self.exists(fullname)

    def _process_result(self, result: TaskResult):
        log_debug(f"Result: {result.success}")
