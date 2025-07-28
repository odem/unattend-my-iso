import os
from typing_extensions import override
from unattend_my_iso.addons.addon_base import UmiAddon
from unattend_my_iso.common.config import TaskConfig, TemplateConfig
from unattend_my_iso.common.logging import log_debug, log_error


class CmdAddon(UmiAddon):
    def __init__(self):
        UmiAddon.__init__(self, "cmd")

    @override
    def integrate_addon(self, args: TaskConfig, template: TemplateConfig) -> bool:

        if self._copy_user_dir(args, template) is False:
            return False
        return True

    def _copy_user_dir(self, args: TaskConfig, template: TemplateConfig) -> bool:
        interpath = self.files._get_path_intermediate(args)
        usersdir = f"{interpath}/umi/users"
        os.makedirs(usersdir, exist_ok=True)

        if template.iso_type != "windows":
            userlist = [
                "root",
                args.addons.answerfile.user_other_name,
                *args.addons.answerfile.additional_users,
            ]
        else:
            userlist = [
                args.addons.answerfile.user_other_name,
                *args.addons.answerfile.additional_users,
            ]

        user_default = args.addons.user.default_user_dir
        userdir_default = self.files._get_path_template_userhome(user_default, args)
        if os.path.exists(userdir_default) is False:
            log_error(f"Default user folder does not exist: {userdir_default}")
            return False

        for user in userlist:
            log_debug(f"Add user  : {user}", "UserAddon")
            dstdir = f"{usersdir}/{user}"
            userdir = self.files._get_path_template_userhome(user, args)
            if os.path.exists(userdir) is False:
                userdir = userdir_default
            copied = self.files.cp(userdir, dstdir)
            if copied is False:
                log_error(f"Failed to copy user folder: {userdir}")
                return copied
        return True
