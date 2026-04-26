import os
from unattend_my_iso.common.const import DIR_SQUASH, NAME_SQUASH
from unattend_my_iso.core.subprocess.caller import run
from unattend_my_iso.common.config import TaskConfig
from unattend_my_iso.core.files.file_manager import UmiFileManager


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
        self._create_squash_image(args, sq_path, sq_umipath)

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
