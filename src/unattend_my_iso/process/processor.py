import os
from unattend_my_iso.helpers import irmod
from unattend_my_iso.helpers.config import IsoTemplate, TaskConfig, TaskResult
from unattend_my_iso.helpers.files import copy_file, copy_folder
from unattend_my_iso.helpers.geniso import generate_md5sum_and_create_iso
from unattend_my_iso.helpers.irmod import create_irmod
from unattend_my_iso.helpers.logging import log_debug
from unattend_my_iso.process.processor_base import TaskProcessorBase


class TaskProcessor(TaskProcessorBase):

    def do_process(self):
        self._print_args(self.taskconfig)
        result = self._process_task(self.taskconfig)
        self._process_result(result)

    def _process_task(self, args: TaskConfig) -> TaskResult:
        name = args.target.template
        if self._ensure_task_template(args) is False:
            return self._get_error_result("No template")

        template = self.templates[name]
        if template is None or self._ensure_task_iso(template) is False:
            return self._get_error_result("No ISO")

        log_debug("Build ISO:")
        if self._extract_iso_contents(args, template) is False:
            return self._get_error_result("Not extracted")

        if self._copy_preseed(args, template) is False:
            return self._get_error_result("Preseed not copied")

        if self._copy_addons(args, template) is False:
            return self._get_error_result("Addons not copied")

        if self._create_irmod(args, template) is False:
            return self._get_error_result("irmod not created")

        if self._generate_iso(args, template) is False:
            return self._get_error_result("iso not generated")

        return self._get_success_result()

    def _generate_iso(self, args: TaskConfig, template: IsoTemplate) -> bool:
        isopath = self.taskconfig.sys.iso_path
        isoname = args.target.template
        interpath = self.taskconfig.sys.intermediate_path
        intername = args.target.template
        fullinter = f"{interpath}/{intername}"
        dst = f"{isopath}/umi_{isoname}"
        hybridmbr = "/usr/lib/ISOLINUX/isohdpfx.bin"
        generate_md5sum_and_create_iso(fullinter, template.iso_name, hybridmbr, dst)
        log_debug(f"Created ISO   : {dst}")

    def _create_irmod(self, args: TaskConfig, template: IsoTemplate) -> bool:
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

    def _copy_addons(self, args: TaskConfig, template: IsoTemplate) -> bool:
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
            if copy_folder(f"{srcgrub}/theme", dstgrub) is False:
                return False
            if copy_file(f"{srcgrub}/grub.cfg", dstgrub) is False:
                return False
            log_debug("Copied addon  : Grub")
        if args.addons.addon_ssh:
            if copy_folder(f"{src}/{template.path_ssh}", dst) is False:
                return False
            log_debug("Copied addon  : Ssh")
        if args.addons.addon_postinstall:
            if copy_folder(f"{src}/{template.path_postinstall}", dst) is False:
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

    def _extract_iso_contents(self, args: TaskConfig, template: IsoTemplate) -> bool:
        interpath = self.taskconfig.sys.intermediate_path
        isopath = self.taskconfig.sys.iso_path
        isoname = template.iso_name
        fulliso = f"{isopath}/{isoname}"
        fulldst = f"{args.sys.mnt_path}/{args.target.template}"
        self._unmount_folder(fulldst)
        if self._mount_folder(fulliso, args.target.template, args.sys.mnt_path):
            copied = copy_folder(fulldst, interpath)
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
