import os
import subprocess
from typing_extensions import override
from unattend_my_iso.addons.addon_base import UmiAddon
from unattend_my_iso.common.config import TaskConfig, TemplateConfig
from unattend_my_iso.common.logging import log_debug, log_error
from unattend_my_iso.common.model import Replaceable


class AnswerFileAddon(UmiAddon):
    def __init__(self):
        UmiAddon.__init__(self, "answerfile")

    @override
    def integrate_addon(self, args: TaskConfig, template: TemplateConfig) -> bool:
        if self.copy_answerfile(args, template) is False:
            return False
        if self.copy_offline_packages(args, template) is False:
            return False
        return True

    def copy_answerfile(self, args: TaskConfig, template: TemplateConfig) -> bool:
        inter = self.files._get_path_intermediate(args)
        interpreseed = f"{inter}/preseed.cfg"
        if template.iso_type == "windows":
            interpreseed = f"{inter}/autounattend.xml"
        srcpreseed = self.get_template_path_optional(
            "answerfile", template.answerfile, args
        )
        if os.path.exists(srcpreseed):
            if self.files.cp(srcpreseed, interpreseed) is False:
                return False
            rules = self._create_replacements(args, interpreseed)
            return self._apply_replacements(rules)
        else:
            log_error(f"Path does not exist: {srcpreseed}", "Answerfile")
        return False

    def copy_offline_packages(self, args: TaskConfig, template: TemplateConfig) -> bool:
        interpath = self.files._get_path_intermediate(args)
        dst = f"{interpath}/umi/packages"
        if os.path.exists(dst) is False:
            os.makedirs(dst, exist_ok=True)
        original_dir = os.getcwd()
        os.chdir(dst)
        packages = args.addons.answerfile.include_offline_packages
        if len(packages) > 0:
            for filename in packages:
                log_debug(f"Copy File {filename}", self.__class__.__qualname__)
                subprocess.run(
                    ["apt", "download", filename],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True,
                )
            os.chdir(original_dir)
        return True

    def _create_replacements(self, args: TaskConfig, preseed: str) -> list[Replaceable]:
        c = args.addons.answerfile
        rules = []
        if os.path.exists(preseed):
            rules += [
                Replaceable(preseed, "CFG_LOCALE_STRING", c.locale_string),
                Replaceable(preseed, "CFG_LOCALE_MULTI", c.locale_multi),
                Replaceable(preseed, "CFG_LOCALE_KEYBOARD", c.locale_keyboard),
                Replaceable(preseed, "CFG_HOST_NAME", c.host_name),
                Replaceable(preseed, "CFG_HOST_DOMAIN", c.host_domain),
                Replaceable(preseed, "CFG_NET_DHCP", "true" if c.net_dhcp else "false"),
                Replaceable(preseed, "CFG_NET_IP", c.net_ip),
                Replaceable(preseed, "CFG_NET_MASK", c.net_mask),
                Replaceable(preseed, "CFG_NET_GATEWAY", c.net_gateway),
                Replaceable(preseed, "CFG_NET_DNS", c.net_dns),
                Replaceable(preseed, "CFG_DISK_CRYPTNAME", c.disk_cryptname),
                Replaceable(preseed, "CFG_DISK_PASSWORD", c.disk_password),
                Replaceable(preseed, "CFG_TIME_UTC", "true" if c.time_utc else "false"),
                Replaceable(preseed, "CFG_TIME_ZONE", c.time_zone),
                Replaceable(preseed, "CFG_TIME_NTP", "true" if c.time_ntp else "false"),
                Replaceable(preseed, "CFG_USER_OTHER_NAME", c.user_other_name),
                Replaceable(preseed, "CFG_USER_OTHER_FULLNAME", c.user_other_fullname),
                Replaceable(preseed, "CFG_USER_OTHER_PASSWORD", c.user_other_password),
                Replaceable(preseed, "CFG_GRUB_INSTALL_DEVICE", c.grub_install_device),
                Replaceable(preseed, "CFG_USER_ROOT_PASSWORD", c.user_root_password),
                Replaceable(
                    preseed,
                    "CFG_USER_ROOT_ENABLED",
                    "true" if c.user_root_enabled else "false",
                ),
                Replaceable(
                    preseed,
                    "CFG_USER_OTHER_ENABLED",
                    "true" if c.user_other_enabled else "false",
                ),
                Replaceable(
                    preseed, "CFG_PACKAGES_INSTALL", " ".join(c.packages_install)
                ),
            ]
        return rules
