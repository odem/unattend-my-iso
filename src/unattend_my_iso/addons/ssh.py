import os
from unattend_my_iso.core.subprocess.caller import run
from typing_extensions import override
from unattend_my_iso.addons.addon_base import UmiAddon
from unattend_my_iso.common.config import TaskConfig, TemplateConfig
from unattend_my_iso.common.logging import log_debug, log_error, log_info


class SshAddon(UmiAddon):
    def __init__(self):
        UmiAddon.__init__(self, "ssh")

    @override
    def integrate_addon(self, args: TaskConfig, template: TemplateConfig) -> bool:
        if self.copy_keyfiles(args) is False:
            return False
        if self.copy_authorized_keys(args) is False:
            return False
        if self.copy_client_config(args) is False:
            return False
        if self.copy_daemon_config(args) is False:
            return False
        return True

    def _get_deployment_keys(self, args: TaskConfig) -> str:
        result = ""
        userlist = args.addons.answerfile.deployment_users
        if args.addons.ssh.config_auth_append_deployment is False:
            return result
        for user in userlist:
            userdir_default = self.files._get_path_template_userhome(user, args)
            if os.path.exists(userdir_default):
                keyfile = f"{userdir_default}/.ssh/id_rsa.pub"
                if os.path.exists(keyfile):
                    log_info(
                        f"Appending deployment key for user : '{user}'",
                        self.__class__.__qualname__,
                    )
                    content = self.files.read_file(keyfile)
                    result = f"\n{result}{content}\n"
        return result

    def copy_authorized_keys(self, args: TaskConfig) -> bool:
        dst = self.files._get_path_intermediate(args)
        dstssh = f"{dst}{args.addons.answerfile.answerfile_hook_dir_cdrom}/ssh"
        dstauth = f"{dstssh}/authorized_keys"
        appendpath = args.addons.ssh.config_auth_append
        appendpath = appendpath.replace("~", args.run.build_homedir)

        srcpath = args.addons.ssh.config_auth
        if srcpath.startswith("~"):
            srcpath = srcpath.replace("~", args.run.build_homedir)
        elif srcpath.startswith("/") is False:
            srcpath = self.get_template_path_optional(
                "ssh", args.addons.ssh.config_auth, args
            )
        if os.path.exists(srcpath):
            log_debug(f"Copy auth keys: {srcpath}", self.__class__.__qualname__)
            os.makedirs(dstssh, exist_ok=True)
            self.files.cp(srcpath, dstauth)
        else:
            os.makedirs(dstssh, exist_ok=True)
            self.files.touch_file(dstauth)

        content = ""
        if os.path.exists(appendpath):
            content = self.files.read_file(appendpath)
        pubkeys_deploy = self._get_deployment_keys(args)
        if pubkeys_deploy != "":
            content = f"{content}\n# Deployment keys{pubkeys_deploy}"

        if content != "":
            return self.files.append_to_file(dstauth, content)
        return True

    def copy_keyfiles(self, args: TaskConfig) -> bool:
        dst = self.files._get_path_intermediate(args)
        keyfile = args.addons.ssh.config_key
        srckeypriv = self.get_template_path_optional(
            "ssh", args.addons.ssh.config_key, args
        )
        if keyfile == "":
            return True

        if srckeypriv == "":
            if args.addons.ssh.keygen:
                dir = self.files._get_path_template(args)
                sshdir = f"{dir}/ssh"
                os.makedirs(sshdir, exist_ok=True)
                srckeypriv = f"{sshdir}/{keyfile}"
                log_debug(f"Generating key: {srckeypriv}", self.__class__.__qualname__)
                if self._generate_key(args, srckeypriv) is False:
                    log_error("Generate key failed", self.__class__.__qualname__)
                    return False
            if keyfile != "" and srckeypriv == "":
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

    def copy_client_config(self, args: TaskConfig) -> bool:
        dst = self.files._get_path_intermediate(args)
        filename = args.addons.ssh.config_client
        srcssh = self.get_template_path_optional("ssh", filename, args)
        dstssh = f"{dst}/umi/ssh/{filename}"
        dstbase = os.path.dirname(dstssh)
        if os.path.exists(srcssh):
            os.makedirs(dstbase, exist_ok=True)
            if filename != "" and os.path.exists(f"{srcssh}"):
                log_debug(
                    f"File Copy : {os.path.basename(srcssh)}",
                    self.__class__.__qualname__,
                )
                if self.files.cp(srcssh, dstssh) is False:
                    return False
            return True
        return False

    def copy_daemon_config(self, args: TaskConfig) -> bool:
        dst = self.files._get_path_intermediate(args)
        filename = args.addons.ssh.config_daemon
        srcssh = self.get_template_path_optional("ssh", filename, args)
        dstssh = f"{dst}/umi/ssh/{filename}"
        dstbase = os.path.dirname(dstssh)
        if os.path.exists(srcssh):
            os.makedirs(dstbase, exist_ok=True)
            if filename != "" and os.path.exists(srcssh):
                log_debug(
                    f"File Copy : {os.path.basename(srcssh)}",
                    self.__class__.__qualname__,
                )
                if self.files.cp(srcssh, dstssh) is False:
                    return False
            return True
        return False

    def _generate_key(self, args: TaskConfig, keyfile: str):
        proc = run(
            ["ssh-keygen", "-f", keyfile, "-N", "", "-C", "digit@isobuilder"],
            input=b"\n",
            capture_output=True,
        )
        if args.run.verbosity >= 4:
            log_debug(f"Keygen output: {proc.stdout}{proc.stderr}")
