import subprocess
import os
import shutil
from unattend_my_iso.common.logging import log_debug, log_error


class UmiIsoGenerator:
    def __init__(self) -> None:
        pass

    def create_iso(
        self, infolder: str, volname: str, outfile: str, user: str, mbrfile: str
    ) -> bool:
        self._generate_md5sum(infolder)
        xorriso_command = self._get_xorriso_cmd(infolder, volname, outfile, mbrfile)
        cmdstr = " ".join(xorriso_command)
        log_debug(f"xorriso cmd  : {cmdstr}")
        out_iso = subprocess.run(
            xorriso_command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if out_iso.returncode != 0:
            log_error(f"xorriso error: {out_iso.stdout}{out_iso.stderr}")
        subprocess.run(["sudo", "chown", f"{user}:{user}", "-R", infolder], check=True)
        return True

    def create_irmod(self, path_mod, path_in, path_inc):
        shutil.rmtree(path_mod, ignore_errors=True)
        os.makedirs(path_mod, exist_ok=True)
        base_dir = os.path.realpath(path_in)
        initrd_path = os.path.join(path_in, "install.amd", "initrd.gz")
        with open(initrd_path, "rb") as initrd_file:
            gzip_process = subprocess.Popen(
                ["gzip", "-d"], stdin=initrd_file, stdout=subprocess.PIPE
            )
            subprocess.run(
                [
                    "sudo",
                    "cpio",
                    "-D",
                    path_mod,
                    "--extract",
                    "--make-directories",
                    "--no-absolute-filenames",
                ],
                stdin=gzip_process.stdout,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
            if gzip_process.stdout is not None:
                gzip_process.stdout.close()
        preseed_src = os.path.join(path_inc, "preseed.cfg")
        preseed_dst = os.path.join(path_mod, "preseed.cfg")
        shutil.copy(preseed_src, preseed_dst)

        subprocess.run(["sudo", "chown", "root:root", preseed_dst], check=True)
        subprocess.run(["sudo", "chmod", "o+w", initrd_path], check=True)
        os.chdir(path_mod)
        subprocess.run(
            "find . | sudo cpio -o -H newc 2>/dev/null | gzip -9 > {}/install.amd/initrd.gz".format(
                base_dir
            ),
            shell=True,
            check=True,
        )
        os.chdir(base_dir)
        subprocess.run(["sudo", "chmod", "o-w", initrd_path], check=True)
        shutil.rmtree(path_mod, ignore_errors=True)

    def _get_xorriso_cmd(self, infolder: str, volname: str, outfile: str, mbrfile: str):
        return [
            "xorriso",
            "-as",
            "mkisofs",
            "-r",
            "-J",
            "-V",
            volname,
            "-c",
            "isolinux/boot.cat",
            "-b",
            "isolinux/isolinux.bin",
            "-no-emul-boot",
            "-boot-info-table",
            "-isohybrid-mbr",
            mbrfile,
            "-partition_offset",
            "16",
            "-isohybrid-gpt-basdat",
            "-eltorito-alt-boot",
            "-eltorito-platform",
            "efi",
            "-e",
            "/boot/grub/efi.img",
            "-no-emul-boot",
            "-o",
            f"{outfile}.iso",
            infolder,
        ]

    def _generate_md5sum(self, infolder: str):
        find_command = f"find {infolder} -type f"
        md5sum_command = (
            f"md5sum $( {find_command} ) > {infolder}/md5sum.txt 2>/dev/null"
        )
        subprocess.run(md5sum_command, shell=True, check=True)
