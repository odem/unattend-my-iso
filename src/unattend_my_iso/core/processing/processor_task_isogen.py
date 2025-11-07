import os
from unattend_my_iso.common.config import TaskResult
from unattend_my_iso.common.config import TaskConfig, TemplateConfig
from unattend_my_iso.core.processing.processor_base import TaskProcessorBase
from unattend_my_iso.common.logging import log_info


class TaskProcessorIsogen(TaskProcessorBase):

    def __init__(self):
        TaskProcessorBase.__init__(self)

    def task_build_all(self, args: TaskConfig) -> TaskResult:
        template = self._get_task_template(args)
        if template is None:
            return self._get_error_result("No template")
        if self._ensure_task_iso(args, template) is False:
            return self._get_error_result("No ISO")
        if self._extract_iso_contents(args, template) is False:
            return self._get_error_result("Not extracted iso")
        if self._extract_virtio_contents(args, template) is False:
            return self._get_error_result("Not extracted virtio")
        if self._copy_addons(args, template) is False:
            return self._get_error_result("Addons not copied")
        if self._prepare_bootloader(args, template) is False:
            return self._get_error_result("irmod not created")
        if self._generate_iso(args, template) is False:
            return self._get_error_result("iso not generated")
        return self._get_success_result()

    def task_extract_iso(self, args: TaskConfig) -> TaskResult:
        template = self._get_task_template(args)
        if template is None:
            return self._get_error_result("No template")
        if self._ensure_task_iso(args, template) is False:
            return self._get_error_result("No ISO")
        if self._extract_iso_contents(args, template) is False:
            return self._get_error_result("Not extracted iso")
        if self._extract_virtio_contents(args, template) is False:
            return self._get_error_result("Not extracted virtio")
        return self._get_success_result()

    def task_build_addons(self, args: TaskConfig) -> TaskResult:
        template = self._get_task_template(args)
        if template is None:
            return self._get_error_result("No template")
        if self._copy_addons(args, template) is False:
            return self._get_error_result("Addons not copied")
        return self._get_success_result()

    def task_build_irmod(self, args: TaskConfig) -> TaskResult:
        template = self._get_task_template(args)
        if template is None:
            return self._get_error_result("No template")
        if self._prepare_bootloader(args, template) is False:
            return self._get_error_result("irmod not created")
        return self._get_success_result()

    def task_build_iso(self, args: TaskConfig) -> TaskResult:
        template = self._get_task_template(args)
        if template is None:
            return self._get_error_result("No template")
        if self._generate_iso(args, template) is False:
            return self._get_error_result("iso not generated")
        return self._get_success_result()

    def _ensure_task_iso(self, args: TaskConfig, template: TemplateConfig) -> bool:
        if template.virtio_name != "":
            srcvirtio = self.files._get_path_isovirtio(args, template)
            if self.exists(srcvirtio):
                log_info("ISO-VIRT is already present", self.__class__.__qualname__)
            else:
                log_info(
                    f"ISO-VIRT requires download ({os.path.basename(srcvirtio)})",
                    self.__class__.__qualname__,
                )
                self._download_file(args, template.virtio_url, template.virtio_name)
            if self.exists(srcvirtio) is False:
                return False

        srciso = self.files._get_path_isosource(args, template)
        if self.exists(srciso):
            log_info(
                f"ISO-OS is already present ({os.path.basename(srciso)})",
                self.__class__.__qualname__,
            )
            return True
        else:
            log_info(
                f"ISO-OS requires download ({os.path.basename(srciso)})",
                self.__class__.__qualname__,
            )
            result = self._download_file(args, template.iso_url, template.iso_name)
            return result

    def _extract_iso_contents(self, args: TaskConfig, template: TemplateConfig) -> bool:
        dir_mount = self.files._get_path_mountpath(args)
        file_mount = self.files._get_path_mountfile(args, template)
        dir_intermediate = self.files._get_path_intermediate(args)
        self.files.unmount_folder(dir_mount)
        if self.files.mount_folder(file_mount, dir_mount):
            os.makedirs(dir_intermediate, exist_ok=True)
            copied = self.files.copy_folder_iso(dir_mount, dir_intermediate)
            copied = self.files.chmod(dir_intermediate, privilege=0o200)
            self.files.unmount_folder(dir_mount)
            if copied:
                log_info(
                    f"ISO-OS successfully extracted ({os.path.basename(file_mount)})",
                    self.__class__.__qualname__,
                )
                return True
        return False

    def _extract_virtio_contents(
        self, args: TaskConfig, template: TemplateConfig
    ) -> bool:
        if template.virtio_name == "":
            return True
        dir_mount = self.files._get_path_mountvirtio(args, template)
        file_mount = self.files._get_path_isovirtio(args, template)
        dir_intermediate = self.files._get_path_intermediate(args)
        dst = f"{dir_intermediate}/umi/virtio"
        if self.files.mount_folder(file_mount, dir_mount, "loop"):
            os.makedirs(dst, exist_ok=True)
            copied = self.files.copy_folder_iso(dir_mount, dst)
            copied = self.files.chmod(dst, privilege=0o200)
            self.files.unmount_folder(dir_mount)
            if copied:
                log_info(f"Copied virt-ISO {file_mount}", self.__class__.__qualname__)
                return True
        return False

    def _copy_addons(self, args: TaskConfig, template: TemplateConfig) -> bool:
        if args.addons.postinstall.postinstall_enabled:
            if self._integrate_addon("postinstall", args, template) is False:
                return False
        if args.addons.answerfile.answerfile_enabled:
            if self._integrate_addon("answerfile", args, template) is False:
                return False
        if args.addons.grub.grub_enabled:
            if self._integrate_addon("grub", args, template) is False:
                return False
        if args.addons.ssh.ssh_enabled:
            if self._integrate_addon("ssh", args, template) is False:
                return False
        if args.addons.user.user_enabled:
            if self._integrate_addon("user", args, template) is False:
                return False
        if args.addons.cmd.cmd_enabled:
            if self._integrate_addon("cmd", args, template) is False:
                return False
        if args.addons.cloudinit.ci_enabled:
            if self._integrate_addon("cloudinit", args, template) is False:
                return False
        return True

    def _prepare_bootloader(self, args: TaskConfig, template: TemplateConfig) -> bool:
        if template.iso_type == "windows":
            return self._create_efidisk_windows(args)
        return self._create_irmod_linux(args)

    def _generate_iso(self, args: TaskConfig, template: TemplateConfig) -> bool:
        dst = self.files._get_path_isopath(args)
        fullinter = self.files._get_path_intermediate(args)
        if self.isogen.create_iso(
            args, template, fullinter, template.name, dst, args.target.file_mbr
        ):
            log_info(
                f"Created ISO {dst}.{args.target.file_extension}",
                self.__class__.__qualname__,
            )
            return True
        return False
