import os
from typing_extensions import override
from unattend_my_iso.addons.addon_base import UmiAddon
from unattend_my_iso.common.config import TaskConfig, TemplateConfig
from unattend_my_iso.common.model import Replaceable


class AnswerFileAddon(UmiAddon):
    def __init__(self):
        UmiAddon.__init__(self, "answerfile")

    @override
    def integrate_addon(self, args: TaskConfig, template: TemplateConfig) -> bool:
        src = self.files._get_path_template(args)
        inter = self.files._get_path_intermediate(args)
        srcpreseed = f"{src}/{template.answerfile}"
        interpreseed = f"{inter}/{template.answerfile}"
        if self.files.cp(srcpreseed, inter) is False:
            return False

        if template.iso_type == "windows":
            srcbackground = f"{src}/{self.addon_name}/background.png"
            dstbackground = f"{inter}/umi/postinstall/images"
            os.makedirs(dstbackground)
            if self.files.cp(srcbackground, dstbackground) is False:
                return False
        return self._apply_replacements(args, interpreseed)

    def _apply_replacements(self, args: TaskConfig, preseed: str) -> bool:
        c = args.addons.answerfile
        rules = [
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
            Replaceable(preseed, "CFG_TIME_UTC", "true" if c.time_utc else "false"),
            Replaceable(preseed, "CFG_TIME_ZONE", c.time_zone),
            Replaceable(preseed, "CFG_TIME_NTP", "true" if c.time_ntp else "false"),
            Replaceable(preseed, "CFG_PACKAGES_INSTALL", " ".join(c.packages_install)),
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
        ]
        for rule in rules:
            self.replacements.append(rule)
        return self.do_replacements()
