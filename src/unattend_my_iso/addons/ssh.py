import os
import subprocess
from typing_extensions import override
from unattend_my_iso.addons.addon_base import UmiAddon
from unattend_my_iso.common.config import TaskConfig, TemplateConfig
from unattend_my_iso.common.logging import log_debug, log_error


class SshAddon(UmiAddon):
    def __init__(self):
        UmiAddon.__init__(self, "ssh")

    @override
    def integrate_addon(self, args: TaskConfig, template: TemplateConfig) -> bool:
        if self.copy_keyfiles(args, template) is False:
            return False
        if self.copy_authorized_keys(args, template) is False:
            return False
        if self.copy_client_config(args, template) is False:
            return False
        if self.copy_daemon_config(args, template) is False:
            return False
        return True

    def copy_keyfiles(self, args: TaskConfig, template: TemplateConfig) -> bool:
        dst = self.files._get_path_intermediate(args)
        keyfile = args.addons.ssh.config_key
        srckeypriv = self.get_template_path_optional(
            "ssh", args.addons.ssh.config_key, args
        )
        if keyfile != "" and srckeypriv == "":
            dir = self.files._get_path_template(args)
            sshdir = f"{dir}/ssh"
            os.makedirs(sshdir, exist_ok=True)
            srckeypriv = f"{sshdir}/{keyfile}"
            log_debug(f"Generating key: {srckeypriv}")
            if args.addons.ssh.keygen:
                if self._generate_key(srckeypriv) is False:
                    log_error("Generate key failed")
                    return False
        if args.addons.ssh.config_key != "" and srckeypriv == "":
            log_error("Source key empty")
            return False

        srckeypub = f"{srckeypriv}.pub"
        dstssh = f"{dst}/umi/ssh"
        if os.path.exists(srckeypriv):
            os.makedirs(dstssh, exist_ok=True)
            if srckeypriv != "" and os.path.exists(srckeypriv):
                log_debug(
                    f"File Copy : {os.path.basename(srckeypriv)}",
                    self.__class__.__qualname__,
                )
                if self.files.cp(srckeypriv, f"{dstssh}/{keyfile}") is False:
                    log_error("Copy key priv failed", self.__class__.__qualname__)
                    return False
                log_debug(
                    f"File Copy : {os.path.basename(srckeypub)}",
                    self.__class__.__qualname__,
                )
                if self.files.cp(srckeypub, f"{dstssh}/{keyfile}.pub") is False:
                    log_error("Copy key pub failed", self.__class__.__qualname__)
                    return False
            return True
        return False

    def copy_authorized_keys(self, args: TaskConfig, template: TemplateConfig) -> bool:
        filename = args.addons.ssh.config_auth
        appendfile = args.addons.ssh.config_auth_append
        srcssh = self.get_template_path_optional("ssh", filename, args)
        dst = self.files._get_path_intermediate(args)
        dstssh = f"{dst}/umi/ssh/{filename}"
        if os.path.exists(srcssh):
            if filename != "" and os.path.exists(srcssh):
                log_debug(
                    f"File Copy : {os.path.basename(srcssh)}",
                    self.__class__.__qualname__,
                )
                if self.files.cp(srcssh, dstssh) is False:
                    return False
                if appendfile != "" and os.path.exists(appendfile):
                    contents = self.files.read_file(appendfile)
                    return self.files.append_to_file(dstssh, contents)
            return True
        return False

    def copy_client_config(self, args: TaskConfig, template: TemplateConfig) -> bool:
        dst = self.files._get_path_intermediate(args)
        filename = args.addons.ssh.config_client
        srcssh = self.get_template_path_optional("ssh", filename, args)
        dstssh = f"{dst}/umi/ssh/{filename}"
        if os.path.exists(srcssh):
            os.makedirs(dstssh, exist_ok=True)
            if filename != "" and os.path.exists(f"{srcssh}"):
                log_debug(
                    f"File Copy : {os.path.basename(srcssh)}",
                    self.__class__.__qualname__,
                )
                if self.files.cp(srcssh, dstssh) is False:
                    return False
            return True
        return False

    def copy_daemon_config(self, args: TaskConfig, template: TemplateConfig) -> bool:
        dst = self.files._get_path_intermediate(args)
        filename = args.addons.ssh.config_daemon
        srcssh = self.get_template_path_optional("ssh", filename, args)
        dstssh = f"{dst}/umi/ssh/{filename}"
        if os.path.exists(srcssh):
            if filename != "" and os.path.exists(srcssh):
                log_debug(
                    f"File Copy : {os.path.basename(srcssh)}",
                    self.__class__.__qualname__,
                )
                if self.files.cp(srcssh, dstssh) is False:
                    return False
            return True
        return False

    def _generate_key(self, keyfile: str):
        msg = "y\n"
        log_debug(f"KEYFILE: {keyfile}")
        subprocess.run(
            ["ssh-keygen", "-q", "-N", "''", "-f", keyfile],
            input=msg.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            capture_output=False,
            text=False,
        )
