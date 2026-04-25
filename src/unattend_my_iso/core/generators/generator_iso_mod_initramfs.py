import os
import shutil
from unattend_my_iso.core.subprocess.caller import run, Popen, PIPE, DEVNULL
from unattend_my_iso.common.logging import log_debug, log_info
from unattend_my_iso.core.files.file_manager import UmiFileManager


class UmiIsoGeneratorModInitramfs:
    def __init__(self) -> None:
        self.files = UmiFileManager()

    def create_irmod(self, path_src: str, path_mod: str, path_in: str):
        if os.path.exists(path_mod):
            shutil.rmtree(path_mod)
        os.makedirs(path_mod)
        base_dir = os.path.realpath(path_in)
        initrd_location = f"{path_in}/{path_src}"
        initrd_filepath = os.path.join(initrd_location, "initrd.gz")
        with open(initrd_filepath, "rb") as initrd_file:
            gzip_process = Popen(["gzip", "-d", "-c"],
                                 stdin=initrd_file, stdout=PIPE)
            run(
                self._get_cpio_cmd_extract(path_mod),
                stdin=gzip_process.stdout,
                stdout=DEVNULL,
                stderr=DEVNULL,
                check=True,
            )
            if gzip_process.stdout is not None:
                gzip_process.stdout.close()
        preseed_src = os.path.join(path_in, "preseed.cfg")
        preseed_dst = os.path.join(path_mod, "preseed.cfg")
        shutil.copy(preseed_src, preseed_dst)
        os.chdir(path_mod)
        cmd = "find . | cpio -o -H newc 2>/dev/null | gzip -9"
        args = f"{cmd} > {{}}/{path_src}/initrd-umi.gz".format(base_dir)
        run(args, shell=True, check=True)
        log_debug(f"Delete irmod : {path_mod}", self.__class__.__qualname__)
        shutil.rmtree(path_mod, ignore_errors=False)
        log_info(f"Created irmod: {path_src}", self.__class__.__qualname__)

    def _get_cpio_cmd_extract(self, path_mod: str) -> list[str]:
        return [
            "fakeroot",
            "cpio",
            "-D",
            path_mod,
            "--extract",
            "--make-directories",
            "--no-absolute-filenames",
        ]
