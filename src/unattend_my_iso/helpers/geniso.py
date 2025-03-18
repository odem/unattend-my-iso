import subprocess

from unattend_my_iso.helpers.logging import log_debug

DIR_MBR_HYBRID = "/usr/lib/ISOLINUX/isohdpfx.bin"


def generate_md5sum_and_create_iso(infolder, volname, outfile, user) -> bool:
    find_command = f"find {infolder} -type f"
    md5sum_command = f"md5sum $( {find_command} ) > {infolder}/md5sum.txt 2>/dev/null"
    subprocess.run(md5sum_command, shell=True, check=True)
    xorriso_command = [
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
        DIR_MBR_HYBRID,
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

    cmdstr = " ".join(xorriso_command)
    log_debug(f"CMD: {cmdstr}")
    out_iso = subprocess.run(
        xorriso_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    if out_iso.returncode != 0:
        log_debug(f"Error on isogen: {out_iso.stdout}{out_iso.stderr}")
    subprocess.run(["sudo", "chown", f"{user}:{user}", "-R", infolder], check=True)
    return True
