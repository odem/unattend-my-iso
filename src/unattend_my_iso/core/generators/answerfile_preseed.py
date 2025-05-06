from unattend_my_iso.common.config import TaskConfig, TemplateConfig
from unattend_my_iso.common.logging import log_debug
from unattend_my_iso.common.model import DIOption


class AnswerfilePreseed:
    def generate_answerfile(
        self, args: TaskConfig, template: TemplateConfig
    ) -> list[DIOption]:
        cfg_locale = self.generate_fragment_locale(args, template)
        cfg_network = self.generate_fragment_network(args, template)
        cfg_mirrors = self.generate_fragment_mirrors(args, template)
        cfg_time = self.generate_fragment_time(args, template)
        cfg_users = self.generate_fragment_users(args, template)
        cfg_packages = self.generate_fragment_packages(args, template)
        cfg_grub = self.generate_fragment_grub(args, template)
        cfg_hooklate = self.generate_fragment_hook_late(args, template)
        return [
            *cfg_locale,
            *cfg_time,
            *cfg_network,
            *cfg_mirrors,
            *cfg_users,
            *cfg_packages,
            *cfg_grub,
            *cfg_hooklate,
        ]

    def generate_fragment_locale(
        self, args: TaskConfig, template: TemplateConfig
    ) -> list[DIOption]:
        c = args.addons.answerfile
        return [
            DIOption("#", "Locale"),
            DIOption("debian-installer/locale", c.locale_string),
            DIOption("localechooser/supported-locales", [c.locale_multi]),
            DIOption("keyboard-configuration/xkb-keymap", c.locale_keyboard, "select"),
        ]

    def generate_fragment_time(
        self, args: TaskConfig, template: TemplateConfig
    ) -> list[DIOption]:
        c = args.addons.answerfile
        return [
            DIOption("#", "Time"),
            DIOption("clock-setup/utc", c.time_utc),
            DIOption("clock-setup/ntp", c.time_ntp),
            DIOption("time/zone", c.time_zone),
        ]

    def generate_fragment_users(
        self, args: TaskConfig, template: TemplateConfig
    ) -> list[DIOption]:
        c = args.addons.answerfile
        return [
            DIOption("#", "Users (root)"),
            DIOption("passwd/root-login", c.user_root_enabled),
            DIOption("passwd/root-password", c.user_root_password, "password"),
            DIOption("passwd/root-password-again", c.user_root_password, "password"),
            DIOption("#", "Users (OTHER)"),
            DIOption("passwd/make-user", c.user_other_enabled),
            DIOption("passwd/user-fullname", c.user_other_fullname),
            DIOption("passwd/username", c.user_other_name),
            DIOption("passwd/user-password", c.user_other_password, "password"),
            DIOption("passwd/user-password-again", c.user_other_password, "password"),
        ]

    def generate_fragment_mirrors(
        self, args: TaskConfig, template: TemplateConfig
    ) -> list[DIOption]:
        c = args.addons.answerfile
        return [
            DIOption("#", "Mirrors"),
            DIOption("mirror/country", "manual"),
            DIOption("mirror/http/hostname", "httpredir.debian.org"),
            DIOption("mirror/http/directory", "/debian"),
            DIOption("mirror/http/proxy", ""),
        ]

    def generate_fragment_grub(
        self, args: TaskConfig, template: TemplateConfig
    ) -> list[DIOption]:
        c = args.addons.answerfile
        return [
            DIOption("#", "Grub"),
            DIOption("grub-installer/only_debian", True),
            DIOption("grub-installer/with_other_os", True),
            DIOption("grub-installer/update-nvram", True),
            DIOption("grub-installer/target", "x86_64-efi"),
            DIOption("grub-installer/efi_secure_boot", False),
            DIOption("grub-installer/choose_bootdev", "", "select"),
            DIOption("grub-installer/skip", False),
            DIOption("grub-installer/bootdev", c.grub_install_device),
        ]

    def generate_fragment_packages(
        self, args: TaskConfig, template: TemplateConfig
    ) -> list[DIOption]:
        c = args.addons.answerfile
        return [
            DIOption("#", "Apt"),
            DIOption("apt-setup/services-select", ["security", "updates"]),
            DIOption("apt-setup/security-host", "security.debian.org"),
            DIOption("apt-setup/use_mirror", True),
            DIOption("apt-setup/cdrom/set-first", False),
            DIOption("apt-setup/cdrom/set-next", False),
            DIOption("apt-setup/cdrom/set-failed", False),
            DIOption("apt-cdrom/detect_progress_title", ""),
            DIOption("apt-cdrom/next", False),
            DIOption("#", "Packages"),
            DIOption("tasksel/first", ["ssh-server"], "multiselect", "tasksel"),
            DIOption("pkgsel/include", c.packages_install),
            DIOption("pkgsel/upgrade", "full-upgrade"),
            DIOption(
                "popularity-contest/participate", False, "boolean", "popularity-contest"
            ),
        ]

    def generate_fragment_network(
        self, args: TaskConfig, template: TemplateConfig
    ) -> list[DIOption]:
        ret = []
        c = args.addons.answerfile
        if c.answerfile_enable_networking:
            ret += [
                DIOption("#", "Networking (Online)"),
                DIOption("netcfg/enable", True),
                DIOption("netcfg/choose_interface", "auto", "select"),
                DIOption("netcfg/get_hostname", c.host_name),
                DIOption("netcfg/get_domain", c.host_domain),
            ]
            if c.answerfile_enable_dhcp:
                ret += [
                    DIOption("netcfg/disable_dhcp", False),
                ]
            else:
                ret += [
                    DIOption("netcfg/disable_dhcp", True),
                    DIOption("netcfg/get_ipadress", c.net_ip),
                    DIOption("netcfg/get_netmask", c.net_mask),
                    DIOption("netcfg/get_gateway", c.net_gateway),
                    DIOption("netcfg/get_nameservers", c.net_dns),
                ]

            ret += [
                DIOption("netcfg/confirm_static", True),
                DIOption("hw-detect/load_firmware", True),
            ]
        else:
            ret += [
                DIOption("#", "Networking (Offline)"),
                DIOption("netcfg/enable", False),
                DIOption("netcfg/choose_interface", "auto", "select"),
                DIOption("netcfg/disable_dhcp", True),
                DIOption("netcfg/get_hostname", c.host_name),
                DIOption("netcfg/get_domain", c.host_domain),
                DIOption("hw-detect/load_firmware", False),
            ]
        return ret

    def generate_fragment_hook_late(
        self, args: TaskConfig, template: TemplateConfig
    ) -> list[DIOption]:
        c = args.addons.answerfile
        cdrom_dir = "/umi"
        target_dir = "/opt/umi"
        filename = "postinstall/postinstall.bash"
        lineprefix = "    "
        linecont = "\\\n"
        cmd_user = f"in-target usermod {c.user_other_name} sudo"
        cmd_dir = f"{lineprefix}mkdir -p /target{target_dir}/;"
        cmd_cp = f"{lineprefix}cp -r /cdrom{cdrom_dir}/* /target{target_dir}/;"
        cmd_chmod = f"{lineprefix}in-target chmod 700 {target_dir}/{filename};"
        cmd_exec = f"{lineprefix}in-target /bin/bash {target_dir}/{filename};"
        cmd_postinstall = f"{cmd_user:79} {linecont}"
        cmd_postinstall += f"{cmd_dir:79} {linecont}"
        cmd_postinstall += f"{cmd_cp:79} {linecont}"
        cmd_postinstall += f"{cmd_chmod:79} {linecont}"
        cmd_postinstall += f"{cmd_exec:79}"
        cmd_full = f"{'':48}{linecont}{cmd_postinstall:75}"
        return [
            DIOption("#", "Hook (Late)"),
            DIOption("preseed/late_command", cmd_full),
        ]
