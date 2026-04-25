import os
from unattend_my_iso.core.generators.generator_iso_mod_initramfs import UmiIsoGeneratorModInitramfs
from unattend_my_iso.core.generators.generator_iso_mod_squash import UmiIsoGeneratorModSquash
from unattend_my_iso.core.subprocess.caller import run
from unattend_my_iso.common.config import TaskConfig, TemplateConfig
from unattend_my_iso.common.logging import log_debug, log_error
from unattend_my_iso.core.files.file_manager import UmiFileManager


class UmiIsoGenerator (UmiIsoGeneratorModInitramfs, UmiIsoGeneratorModSquash):

    def __init__(self) -> None:
        UmiIsoGeneratorModInitramfs.__init__(self)
        UmiIsoGeneratorModSquash.__init__(self)
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
            log_debug(f"xorriso cmd  : {cmdstr}", self.__class__.__qualname__)
        out_iso = run(
            xorriso_command,
            capture_output=True,
            text=True,
        )
        if out_iso.returncode != 0:
            log_error(
                f"xorriso error: {out_iso.stdout}{out_iso.stderr}",
                self.__class__.__qualname__,
            )
        return True

    def create_efidisk_windows(self, args: TaskConfig, infolder: str):
        mntpath = args.sys.path_mnt
        dstmount = f"{mntpath}/efiboot"
        dstmgr = f"{dstmount}/efi/boot"
        srcefi = f"{infolder}/efiboot.img"

        # Create
        log_debug(f"Create disk  : {infolder}/efiboot.img")
        run(
            ["dd", "if=/dev/zero", f"of={srcefi}", "bs=1M", "count=64"],
            capture_output=True,
            text=True,
        )

        # Format
        log_debug(f"Format disk  : {infolder}/efiboot.img")
        run(
            ["/usr/sbin/mkfs.fat", "-F32", f"{infolder}/efiboot.img"],
            capture_output=True,
            text=True,
        )

        # Mount
        log_debug(f"Mount efi    : {dstmount}")
        os.makedirs(dstmount, exist_ok=True)
        self.files.mount_folder(srcefi, dstmount, "loop")
        run(["sudo", "mkdir", "-p", f"{dstmount}/efi/boot"])

        # Extract
        log_debug(f"Extract mgr  : {dstmgr}")
        run(
            self._get_wimlib_cmd_extract(infolder, dstmgr),
            capture_output=True,
            text=True,
        )
        run(["sudo", "mv", f"{dstmgr}/bootmgfw.efi", f"{dstmgr}/bootx64.efi"])
        self.files.unmount_folder(dstmount)

    def _generate_md5sum(self, infolder: str):
        find_command = f"find {infolder} -type f"
        cmd = f"md5sum $( {find_command} ) > {infolder}/md5sum.txt 2>/dev/null"
        try:
            proc = run(cmd, shell=True, check=True,
                       capture_output=True, text=True)
            if proc.returncode != 0:
                log_error(
                    f"Error on md5sum: {proc.stdout}{proc.stderr}",
                    self.__class__.__qualname__,
                )
        except Exception as exe:
            log_error(f"Exception on md5sum: {exe}",
                      self.__class__.__qualname__)

    def _get_wimlib_cmd_extract(self, infolder: str, dstmgr: str) -> list[str]:
        return [
            "sudo",
            "wimlib-imagex",
            "extract",
            f"{infolder}/sources/boot.wim",
            "1",
            "Windows/Boot/EFI/bootmgfw.efi",
            f"--dest-dir={dstmgr}",
        ]

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
            "-joliet",
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
