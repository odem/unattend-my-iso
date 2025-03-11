import subprocess
import os


def generate_md5sum_and_create_iso(infolder, volname, hybridmbr, outfile):
    # Step 1: Generate md5sum.txt for all files in INFOLDER
    find_command = f"find {infolder} -type f"
    md5sum_command = f"md5sum $( {find_command} ) > {infolder}/md5sum.txt 2>/dev/null"

    # Execute the md5sum command
    subprocess.run(md5sum_command, shell=True, check=True)

    # Step 2: Create ISO using xorriso
    xorriso_command = [
        "xorriso",
        "-as",
        "mkisofs",
        "-r",  # Rock Ridge extensions
        "-J",  # Joliet extensions
        "-V",
        volname,  # Volume name
        "-c",
        "isolinux/boot.cat",  # Boot catalog
        "-b",
        "isolinux/isolinux.bin",  # Bootable binary
        "-no-emul-boot",  # No emulation
        "-boot-info-table",  # Boot info table
        "-isohybrid-mbr",
        hybridmbr,  # Hybrid MBR
        "-partition_offset",
        "16",  # Partition offset
        "-isohybrid-gpt-basdat",  # GPT support
        "-eltorito-alt-boot",  # Alternative boot
        "-eltorito-platform",
        "efi",  # EFI platform
        "-e",
        "/boot/grub/efi.img",  # EFI boot image
        "-no-emul-boot",  # No emulation for EFI
        "-o",
        f"{outfile}.iso",  # Output ISO file
        infolder,  # Input folder
    ]

    # Execute the xorriso command
    subprocess.run(
        xorriso_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
