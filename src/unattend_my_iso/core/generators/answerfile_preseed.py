from unattend_my_iso.common.config import TaskConfig, TemplateConfig
from unattend_my_iso.common.model import DIOption
from unattend_my_iso.core.generators.answerfile_commands import AnswerfileCommands
from unattend_my_iso.core.generators.answerfile_recipe import AnswerfileRecipe

RECIPE_NAME = "custom-lvm"


class AnswerfilePreseed:
    def generate_answerfile(
        self, args: TaskConfig, template: TemplateConfig
    ) -> list[DIOption]:
        cfg_locale = self.generate_fragment_locale(args, template)
        cfg_network = self.generate_fragment_network(args, template)
        cfg_partman = self.generate_fragment_partman(args, template)
        cfg_mirrors = self.generate_fragment_mirrors(args, template)
        cfg_time = self.generate_fragment_time(args, template)
        cfg_users = self.generate_fragment_users(args, template)
        cfg_packages = self.generate_fragment_packages(args, template)
        cfg_grub = self.generate_fragment_grub(args, template)
        cfg_hooklate = self.generate_fragment_hook_late(args, template)
        cfg_reboot = self.generate_fragment_reboot(args, template)
        return [
            *cfg_locale,
            *cfg_time,
            *cfg_network,
            *cfg_partman,
            *cfg_mirrors,
            *cfg_users,
            *cfg_packages,
            *cfg_grub,
            *cfg_hooklate,
            *cfg_reboot,
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
        result = []
        result += [
            DIOption("#", "Apt"),
            DIOption("apt-setup/use_mirror", c.answerfile_enable_networking),
            DIOption("apt-setup/services-select", ["security", "updates"]),
            DIOption("apt-setup/security-host", "security.debian.org"),
            DIOption("apt-setup/cdrom/set-first", False),
            DIOption("apt-setup/cdrom/set-next", False),
            DIOption("apt-setup/cdrom/set-failed", False),
            DIOption("apt-cdrom/detect_progress_title", ""),
            DIOption("apt-cdrom/next", False),
        ]
        result += [
            DIOption("#", "Packages"),
            DIOption("tasksel/first", ["ssh-server", "sudo"], "multiselect", "tasksel"),
            DIOption("pkgsel/upgrade", "full-upgrade"),
            DIOption("pkgsel/include", c.packages_install),
            DIOption("#", "Popularity Contest"),
            DIOption(
                "popularity-contest/participate", False, "boolean", "popularity-contest"
            ),
        ]
        return result

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
        cfg = args.addons.answerfile
        cdrom_dir = cfg.answerfile_hook_dir_cdrom
        target_dir = cfg.answerfile_hook_dir_target
        filename = cfg.answerfile_hook_filename
        cmdlist = [
            f"mkdir -p /target{target_dir}/",
            f"cp -r /cdrom{cdrom_dir}/* /target{target_dir}/",
        ]
        if args.addons.postinstall.postinstall_enabled:
            cmdlist += [
                f"in-target chmod 700 {target_dir}/{filename}",
                f"in-target /bin/bash {target_dir}/{filename}",
            ]
        cmd = AnswerfileCommands()
        cmd_full = cmd.generate_fragment_hook_late(cmdlist, args, template)
        return [
            DIOption("#", "Hook (Late)"),
            DIOption("preseed/late_command", cmd_full),
        ]

    def generate_fragment_partman(
        self, args: TaskConfig, template: TemplateConfig
    ) -> list[DIOption]:
        c = args.addons.answerfile
        result = []
        result += [
            DIOption("#", "Partman"),
            DIOption("partman-auto/disk", "", "select"),
            DIOption("partman-partitioning/default_label", "gpt"),
            DIOption("partman-partitioning/choose_label", "gpt"),
            DIOption("partman-partitioning/confirm_write_new_label", True),
            DIOption("partman-lvm/device_remove_lvm", True),
            DIOption("partman-lvm/confirm", True),
            DIOption("partman-lvm/confirm_nooverwrite", True),
            DIOption("partman-md/device_remove_md", True),
        ]
        if c.answerfile_enable_crypto:
            result += [
                DIOption("#", "Partman (CRYPTO)"),
                DIOption("partman-auto/method", "crypto"),
                DIOption("partman-auto/choose_recipe", "autocrypt-recipe", "select"),
                DIOption("partman-auto/expert_recipe_file", "/autocrypt-recipe"),
                DIOption("partman-crypto/encrypt", "luks"),
                DIOption("partman-crypto/guided_size", "max"),
                DIOption("partman-crypto/passphrase", c.disk_password),
                DIOption("partman-crypto/passphrase-again", c.disk_password),
                DIOption("partman-cryptsetup/passphrase", c.disk_password),
                DIOption("partman-crypto/confirm", True),
                DIOption("partman-auto-crypto/erase_disks", False),
                DIOption("#", "Partman-auto"),
                DIOption("partman-lvm/lv_size", "100%"),
                DIOption("partman-auto-lvm/lv_size", "100%"),
                DIOption("partman-auto-lvm/guided_size", "100%"),
                DIOption("partman-auto-lvm/new_vg_name", c.disk_lvm_vg),
                DIOption("partman-auto/choose_recipe", RECIPE_NAME),
                DIOption(
                    "partman-auto/init_automatically_partition",
                    "biggest_free",
                    "select",
                ),
            ]
        else:
            if c.answerfile_enable_lvm:
                result += [
                    DIOption("#", "Partman (LVM)"),
                    DIOption("partman-auto/method", "lvm"),
                    DIOption("partman-auto-lvm/guided_size", "max"),
                    DIOption("partman-auto-lvm/new_vg_name", c.disk_lvm_vg),
                    DIOption("partman-auto-lvm/choose_recipe", RECIPE_NAME, "select"),
                ]
            else:
                result += [
                    DIOption("#", "Partman (Regular)"),
                    DIOption("partman-auto/method", "regular"),
                    DIOption("partman-auto/choose_recipe", RECIPE_NAME),
                ]

        result += self.generate_fragment_recipe(args, template)
        result += [
            DIOption("#", "Partman (Confirm)"),
            DIOption("partman/confirm", True),
            DIOption("partman/confirm_nooverwrite", True),
            DIOption("partman-partitioning/confirm_write_new_label", True),
        ]
        if c.answerfile_confirm_partitioning:
            result += [
                DIOption("partman/confirm_write_new_label", True),
                DIOption("partman/choose_partition", "finish", "select"),
            ]

        return result

    def generate_fragment_reboot(
        self, args: TaskConfig, template: TemplateConfig
    ) -> list[DIOption]:
        result = []
        c = args.addons.answerfile
        if c.answerfile_confirm_final_reboot:
            result += [
                DIOption("#", "Confirm Reboot"),
                DIOption("finish-install/reboot_in_progress", "", "note"),
                DIOption("debian-installer/exit/reboot", True),
            ]
        return result

    def generate_fragment_recipe(
        self, args: TaskConfig, template: TemplateConfig
    ) -> list[DIOption]:
        recipe = AnswerfileRecipe()
        recipe = recipe.generate_recipe(RECIPE_NAME, args.addons.answerfile.disk_lvm_vg)
        return [
            DIOption("#", "Recipe (LVM+LUKS)"),
            DIOption("partman-auto/expert_recipe", recipe),
        ]
