import subprocess
import os
import shutil
from unattend_my_iso.common.config import TaskConfig, TemplateConfig
from unattend_my_iso.common.logging import log_debug, log_error, log_info
from unattend_my_iso.core.files.file_manager import UmiFileManager


class UmiIsoGenerator:
    def __init__(self) -> None:
        self.files = UmiFileManager()

    def create_iso(
        self,
        args: TaskConfig,
        template: TemplateConfig,
        infolder: str,
        volname: str,
        outfile: str,
        mbrfile: str,
    ) -> bool:
        self._generate_md5sum(infolder)

        if template.iso_type == "windows":
            xorriso_command = self._get_xorriso_cmd_windows(infolder, outfile)
        else:
            xorriso_command = self._get_xorriso_cmd_linux(
                infolder, volname, outfile, mbrfile
            )

        cmdstr = " ".join(xorriso_command)
        if args.run.verbosity >= 4:
            log_debug(f"xorriso cmd  : {cmdstr}")
        out_iso = subprocess.run(
            xorriso_command,
            capture_output=True,
            text=True,
        )
        if out_iso.returncode != 0:
            log_error(f"xorriso error: {out_iso.stdout}{out_iso.stderr}")
        return True

    def create_irmod(self, path_src: str, path_mod: str, path_in: str):
        if os.path.exists(path_mod):
            shutil.rmtree(path_mod)
        os.makedirs(path_mod)
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
            if gzip_process.stdout is not None:
                gzip_process.stdout.close()
        preseed_src = os.path.join(path_in, "preseed.cfg")
        preseed_dst = os.path.join(path_mod, "preseed.cfg")
        shutil.copy(preseed_src, preseed_dst)
        os.chdir(path_mod)
        subprocess.run(
            f"find . | cpio -o -H newc 2>/dev/null | gzip -9 > {{}}/{path_src}/initrd-umi.gz".format(
                base_dir
            ),
            shell=True,
            check=True,
        )
        log_debug(f"Delete irmod : {path_mod}")
        shutil.rmtree(path_mod, ignore_errors=False)
        log_info(f"Created irmod: {path_src}")

    def create_efidisk_windows(self, args: TaskConfig, infolder: str):
        mntpath = args.sys.path_mnt
        dstmount = f"{mntpath}/efiboot"
        dstmgr = f"{dstmount}/efi/boot"
        srcefi = f"{infolder}/efiboot.img"
        subprocess.run(
            ["dd", "if=/dev/zero", f"of={srcefi}", "bs=1M", "count=64"],
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["/usr/sbin/mkfs.fat", "-F32", f"{infolder}/efiboot.img"],
            capture_output=True,
            text=True,
        )
        log_debug(f"Create efi   : {infolder}/efiboot.img")
        os.makedirs(dstmount, exist_ok=True)
        self.files.mount_folder(srcefi, dstmount, "loop")
        subprocess.run(["sudo", "mkdir", "-p", f"{dstmount}/efi/boot"])
        subprocess.run(
            [
                "sudo",
                "wimlib-imagex",
                "extract",
                f"{infolder}/sources/boot.wim",
                "1",
                "Windows/Boot/EFI/bootmgfw.efi",
                f"--dest-dir={dstmgr}",
            ],
            capture_output=True,
            text=True,
        )
        subprocess.run(
            [
                "sudo",
                "mv",
                f"{dstmgr}/bootmgfw.efi",
                f"{dstmgr}/bootx64.efi",
            ]
        )
        self.files.unmount_folder(dstmount)

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

    def _get_xorriso_cmd_windows(self, infolder: str, outfile: str):
        return [
            "xorriso",
            "-as",
            "mkisofs",
            "-iso-level",
            "3",
            "-full-iso9660-filenames",
            "-volid",
            "win11",
            "-eltorito-boot",
            "boot/etfsboot.com",
            "-eltorito-catalog",
            "boot/boot.cat",
            "-no-emul-boot",
            "-boot-load-size",
            "8",
            "-boot-info-table",
            "-eltorito-alt-boot",
            "-e",
            "efiboot.img",
            "-no-emul-boot",
            "-isohybrid-mbr",
            "/usr/lib/ISOLINUX/isohdpfx.bin",
            "-isohybrid-gpt-basdat",
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
