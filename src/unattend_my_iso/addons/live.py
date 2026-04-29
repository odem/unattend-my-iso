import os
import re
import glob
from typing_extensions import override
from unattend_my_iso.addons.addon_base import UmiAddon
from unattend_my_iso.common.config import TaskConfig, TemplateConfig
from unattend_my_iso.common.const import DIR_SQUASH
from unattend_my_iso.common.logging import log_error, log_info
from unattend_my_iso.core.subprocess.caller import run


class LiveBootAddon(UmiAddon):
    topic: str

    def __init__(self):
        UmiAddon.__init__(self, "live")
        self.topic = self.__class__.__qualname__

    @override
    def integrate_addon(self, args: TaskConfig, template: TemplateConfig) -> bool:
        if self._copy_addon_data_umidir(args) is False:
            return False
        if self._copy_addon_data_scripts(args) is False:
            return False
        if self._copy_addon_data_launcher(args) is False:
            return False
        if self._exec_squashfs_scripts(args) is False:
            return False
        return True

    def _copy_addon_data_umidir(self, args: TaskConfig):
        cfglive = args.addons.live
        interpath = self.files._get_path_intermediate(args)
        os.chdir(args.sys.path_cwd)
        dstsquash = f"{interpath}/{cfglive.live_boot_type}/{DIR_SQUASH}"
        dstumi = f"{dstsquash}/opt/umi"
        src_umi = f"{interpath}/umi"
        if cfglive.live_copy_umidir:
            if self.files.exists(src_umi):
                self.files.cp(src_umi, dstumi)
            else:
                log_error(f"UMI dir not found: {src_umi}", self.topic)

    def _copy_addon_data_launcher(self, args: TaskConfig):
        cfglive = args.addons.live
        os.chdir(args.sys.path_cwd)
        livepath = self.files._get_path_template_addon("live", args)
        interpath = self.files._get_path_intermediate(args)
        src_launcher = f"{livepath}/launcher"
        dstsquash = f"{interpath}/{cfglive.live_boot_type}/{DIR_SQUASH}"
        dst_launcher = f"{dstsquash}/usr/share/applications"
        dst_dsklinks = f"{dstsquash}/home/user/Desktop"
        for launcher in cfglive.live_copy_launchers:
            srcitem = f"{src_launcher}/{launcher}"
            if self.files.exists(srcitem):
                os.makedirs(dst_dsklinks, exist_ok=True)
                self.files.cp(srcitem, dst_launcher)
                self.files.cp(srcitem, dst_dsklinks)
                run(["sudo", "chown", "1000:1000", "-R", dst_launcher])
                run(["sudo", "chmod", "+x", "-R", dst_launcher])
            else:
                log_error(f"File not found: {srcitem}", self.topic)

    def _copy_addon_data_scripts(self, args: TaskConfig):
        cfglive = args.addons.live
        os.chdir(args.sys.path_cwd)
        postpath = self.files._get_path_template_addon("postinstall", args)
        interpath = self.files._get_path_intermediate(args)
        dstsquash = f"{interpath}/{cfglive.live_boot_type}/{DIR_SQUASH}"
        dst_scripts = f"{dstsquash}/usr/local/bin/"
        for script in cfglive.live_copy_scripts:
            srcitem = f"{postpath}/{script}"
            if self.files.exists(srcitem):
                self.files.cp(srcitem, dst_scripts)
            else:
                log_error(f"File not found: {srcitem}", self.topic)

    def _exec_squashfs_scripts(self, args: TaskConfig):
        cfglive = args.addons.live
        interpath = self.files._get_path_intermediate(args)
        dstsquash = f"{interpath}/{cfglive.live_boot_type}/{DIR_SQUASH}"
        if cfglive.live_boot_type != "":
            if len(cfglive.live_squashfs_execute) > 0:
                log_info("Executing squashfs script:")
                run(["sudo", "mount", "/dev", f"{dstsquash}/dev"])
                run(["sudo", "mount", "/dev/pts", f"{dstsquash}/dev/pts"])
                run(["sudo", "mount", "/run", f"{dstsquash}/run"])
                run(["sudo", "mount", "/proc", f"{dstsquash}/proc"])

                for scriptfile in cfglive.live_squashfs_execute:
                    run(["sudo", "chroot", dstsquash,
                        "/bin/bash", "-c", scriptfile, self._extract_kernel_version])

                run(["sudo", "mount", "/proc", f"{dstsquash}/proc"])
                run(["sudo", "mount", "/run", f"{dstsquash}/run"])
                run(["sudo", "mount", "/dev/pts", f"{dstsquash}/dev/pts"])
                run(["sudo", "mount", "/dev", f"{dstsquash}/dev"])

    def _extract_kernel_version(self, path: str) -> str:
        searchfolder = f"{path}/boot"
        pattern = f"{searchfolder}/initrd.img*"
        files = glob.glob(pattern)
        version_regex = re.compile(r"initrd\.img-(.+)")
        for file in files:
            match = version_regex.search(file)
            if match:
                kernel_version = match.group(1)
                return kernel_version
        return "X.Y.Z-W"
