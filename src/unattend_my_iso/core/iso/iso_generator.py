import subprocess
import os
import shutil
from unattend_my_iso.common.logging import log_debug, log_error, log_info


class UmiIsoGenerator:
    def __init__(self) -> None:
        pass

    def create_iso_linux(
        self, infolder: str, volname: str, outfile: str, user: str, mbrfile: str
    ) -> bool:
        self._generate_md5sum(infolder)
        xorriso_command = self._get_xorriso_cmd_linux(
            infolder, volname, outfile, mbrfile
        )
        cmdstr = " ".join(xorriso_command)
        log_debug(f"xorriso cmd  : {cmdstr}")
        out_iso = subprocess.run(
            xorriso_command,
            check=True,
            capture_output=True,
            text=True,
        )
        if out_iso.returncode != 0:
            log_error(f"xorriso error: {out_iso.stdout}{out_iso.stderr}")
        subprocess.run(["sudo", "chown", f"{user}:{user}", "-R", infolder], check=True)
        return True

    def create_irmod(self, path_src: str, path_mod: str, path_in: str, path_inc: str):
        if os.path.exists(path_mod):
            shutil.rmtree(path_mod)
        os.makedirs(path_mod)
        # user = "jb"
        # subprocess.run(["sudo", "chown", f"{user}:{user}", "-R", path_mod], check=True)
        base_dir = os.path.realpath(path_in)
        initrd_location = f"{path_in}/{path_src}"
        initrd_filepath = os.path.join(initrd_location, "initrd.gz")
        with open(initrd_filepath, "rb") as initrd_file:
            gzip_process = subprocess.Popen(
                ["gzip", "-d", "-c"], stdin=initrd_file, stdout=subprocess.PIPE
            )
            subprocess.run(
                [
                    "fakeroot",
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
            subprocess.run(["sudo", "chown", "jb:jb", "-R", path_mod], check=True)
            if gzip_process.stdout is not None:
                gzip_process.stdout.close()
        preseed_src = os.path.join(path_in, "preseed.cfg")
        preseed_dst = os.path.join(path_mod, "preseed.cfg")
        shutil.copy(preseed_src, preseed_dst)

        # subprocess.run(["sudo", "chown", "root:root", path_mod], check=True)
        # subprocess.run(["sudo", "chmod", "o+w", initrd_filepath], check=True)
        os.chdir(path_mod)
        subprocess.run(
            # f"find . | sudo cpio -o -H newc 2>/dev/null | gzip -9 > {{}}/{path_src}/initrd.gz".format(
            f"find . | cpio -o -H newc 2>/dev/null | gzip -9 > {{}}/{path_src}/initrd-umi.gz".format(
                base_dir
            ),
            shell=True,
            check=True,
        )
        os.chdir(base_dir)
        # subprocess.run(["sudo", "chown", f"{user}:{user}", "-R", path_mod], check=True)
        # subprocess.run(["sudo", "chmod", "a+w", "-R", path_mod], check=True)
        shutil.rmtree(path_mod, ignore_errors=True)
        # subprocess.run(["sudo", "chmod", "o-w", initrd_filepath], check=True)
        subprocess.run(["rm", "-rf", path_mod], check=True)
        log_info(f"Created irmod : {path_src}")

    def _get_xorriso_cmd_linux(
        self, infolder: str, volname: str, outfile: str, mbrfile: str
    ):
        return [
            "xorriso",
            "-as",
            "mkisofs",
            "-r",
            "-J",
            "-R",
            "-iso-level",
            "3",
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

    def _get_xorriso_cmd_windows(
        self, infolder: str, volname: str, outfile: str, mbrfile: str
    ):
        return [
            "xorriso",
            "-as",
            "mkisofs",
            "-r",
            "-J",
            "-R",
            "-iso-level",
            "3",
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
        try:
            proc = subprocess.run(
                md5sum_command, shell=True, check=True, capture_output=True, text=True
            )
            if proc.returncode != 0:
                log_error(f"Error on md5sum: {proc.stdout}{proc.stderr}")
        except Exception as exe:
            log_error(f"Exception on md5sum: {exe}")
