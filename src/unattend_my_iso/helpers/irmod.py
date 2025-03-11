import os
import shutil
import subprocess


def create_irmod(path_mod, path_in, path_inc):
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
