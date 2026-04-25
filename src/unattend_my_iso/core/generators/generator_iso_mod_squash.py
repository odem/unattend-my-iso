import os
from unattend_my_iso.core.subprocess.caller import run
from unattend_my_iso.common.config import TaskConfig
from unattend_my_iso.common.logging import log_error
from unattend_my_iso.core.files.file_manager import UmiFileManager

DIR_SQUASH = "squashfs"
NAME_SQUASH = "filesystem.squashfs"


class UmiIsoGeneratorModSquash:
    topic: str

    def __init__(self) -> None:
        self.topic = self.__class__.__qualname__
        self.files = UmiFileManager()

    def create_squashmod(
        self, args: TaskConfig, path_src: str, path_mod: str, path_in: str
    ):
        cfglive = args.addons.live
        interpath = self.files._get_path_intermediate(args)
        os.chdir(args.sys.path_cwd)
        dstsquash = f"{interpath}/{cfglive.live_boot_type}/{DIR_SQUASH}"
        os.makedirs(path_mod, exist_ok=True)
        os.makedirs(dstsquash, exist_ok=True)
        base_dir = os.path.realpath(path_in)
        sq_loc = f"{base_dir}/{path_src}"
        sq_path = os.path.join(sq_loc, NAME_SQUASH)
        sq_umipath = os.path.join(sq_loc, f"umi-{NAME_SQUASH}")
        self._copy_original_data(args, sq_path)
        self._copy_addon_data_umidir(args)
        self._copy_addon_data_launcher(args)
        self._copy_addon_data_scripts(args)
        self._create_squash_image(args, sq_path, sq_umipath)

    def _copy_original_data(self, args: TaskConfig, squash_filepath: str):
        mntpath = args.sys.path_mnt
        os.chdir(args.sys.path_cwd)
        dstmount = f"{mntpath}/{DIR_SQUASH}"
        self.files.mount_folder(squash_filepath, dstmount, "loop", DIR_SQUASH)
        run(self._create_command_rsync(args, dstmount))
        self.files.unmount_folder(dstmount)

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

    def _create_squash_image(self, args: TaskConfig, sq_path: str, sq_umipath: str):
        cfglive = args.addons.live
        interpath = self.files._get_path_intermediate(args)
        os.chdir(args.sys.path_cwd)
        dstsquash = f"{interpath}/{cfglive.live_boot_type}/{DIR_SQUASH}"
        run(["sudo", "rm", "-rf", sq_umipath])
        run(self._create_command_squashfs(dstsquash, sq_umipath))
        run(["sudo", "rm", "-rf", sq_path])
        run(["sudo", "rm", "-rf", dstsquash])
        run(["sudo", "mv", sq_umipath, sq_path])

    def _create_command_squashfs(self, dstsquash: str, sq_umipath: str) -> list[str]:
        return ["sudo",
                "mksquashfs",
                dstsquash,
                sq_umipath,
                "-quiet",
                "-progress",
                ]

    def _create_command_rsync(self, args: TaskConfig, dstmount: str) -> list[str]:
        cfglive = args.addons.live
        interpath = self.files._get_path_intermediate(args)
        return ["sudo",
                "rsync",
                "-a",
                "--info=progress2",
                f"{dstmount}",
                f"{interpath}/{cfglive.live_boot_type}/",
                ]
