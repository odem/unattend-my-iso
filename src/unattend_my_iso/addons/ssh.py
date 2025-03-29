import os
import subprocess
from typing_extensions import override
from unattend_my_iso.addons.addon_base import UmiAddon
from unattend_my_iso.common.config import TaskConfig, TemplateConfig
from unattend_my_iso.common.logging import log_debug, log_error


class SshAddon(UmiAddon):
    def __init__(self):
        UmiAddon.__init__(self, "ssh")

    def _generate_key(self, keyfile: str):
        msg = "y\n"
        subprocess.run(["ssh-keygen", "-N", "''", "-f", keyfile], input=msg.encode())

    def read_file(self, filename: str) -> str:
        try:
            with open(filename, "r") as file:
                return file.read()
        except Exception as e:
            log_error(f"Exception on file append: {e}")
        return ""

    def append_to_file(self, filename: str, text_to_append: str):
        try:
            with open(filename, "a") as file:
                file.write(text_to_append)
        except Exception as e:
            log_error(f"Exception on file append: {e}")

    @override
    def integrate_addon(self, args: TaskConfig, template: TemplateConfig) -> bool:
        templatepath = args.sys.template_path
        templatename = args.target.template
        interpath = args.sys.intermediate_path
        intername = args.target.template
        f_client = args.addons.ssh.config_client
        f_daemon = args.addons.ssh.config_daemon
        f_auth = args.addons.ssh.config_auth
        f_authapp = args.addons.ssh.config_auth_append
        f_key = args.addons.ssh.config_key
        dst = f"{interpath}/{intername}"
        src = f"{templatepath}/{templatename}"
        srcssh = f"{src}/{template.path_ssh}"
        dstssh = f"{dst}/umi/ssh"
        srcsshkey = f"{srcssh}/{f_key}"

        os.makedirs(dstssh, exist_ok=True)
        if args.addons.ssh.keygen:
            if self._generate_key(srcsshkey) is False:
                return False
        if f_key != "" and os.path.exists(srcsshkey):
            log_debug(f"File Copy   : {srcsshkey}")
            if self.files.cp(srcsshkey, f"{dstssh}/{f_key}") is False:
                return False
            log_debug(f"File Copy   : {srcssh}/{f_key}.pub")
            if self.files.cp(f"{srcssh}/{f_key}.pub", f"{dstssh}/{f_key}.pub") is False:
                return False
        if f_client != "" and os.path.exists(f"{srcssh}/{f_client}"):
            log_debug(f"File Copy   : {srcssh}/{f_client}")
            if self.files.cp(f"{srcssh}/{f_client}", f"{dstssh}/{f_client}") is False:
                return False
        if f_daemon != "" and os.path.exists(f"{srcssh}/{f_daemon}"):
            log_debug(f"File Copy   : {srcssh}/{f_daemon}")
            if self.files.cp(f"{srcssh}/{f_daemon}", f"{dstssh}/{f_daemon}") is False:
                return False
        if f_auth != "" and os.path.exists(f"{srcssh}/{f_auth}"):
            log_debug(f"File Copy   : {srcssh}/{f_auth}")
            if self.files.cp(f"{srcssh}/{f_auth}", f"{dstssh}/{f_auth}") is False:
                return False
            if f_authapp != "" and os.path.exists(f_authapp):
                contents = self.read_file(f_authapp)
                self.append_to_file(f"{dstssh}/{f_auth}", contents)

        return True
