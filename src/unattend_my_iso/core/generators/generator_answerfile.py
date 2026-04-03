from unattend_my_iso.common.config import TaskConfig
from unattend_my_iso.common.const import (
    DEFAULT_PASSWORD,
    DEFAULT_USERNAME,
    RECIPE_NAME,
)
from unattend_my_iso.common.logging import log_warn
from unattend_my_iso.common.model import DIOption
from unattend_my_iso.core.generators.generator_recipe import (
    LINE_CONT,
    LINE_PREFIX,
    AnswerfileRecipe,
)


class AnswerfilePreseed:
    def generate_answerfile(self, args: TaskConfig) -> list[DIOption]:
        cfg_hookearly = self.generate_fragment_hook_early(args)
        cfg_locale = self.generate_fragment_locale(args)
        cfg_network = self.generate_fragment_network(args)
        cfg_partman = self.generate_fragment_partman(args)
        cfg_mirrors = self.generate_fragment_mirrors()
        cfg_time = self.generate_fragment_time(args)
        cfg_users = self.generate_fragment_users(args)
        cfg_packages = self.generate_fragment_packages(args)
        cfg_grub = self.generate_fragment_grub(args)
        cfg_hooklate = self.generate_fragment_hook_late(args)
        cfg_reboot = self.generate_fragment_reboot(args)
        return [
            *cfg_hookearly,
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

    def generate_fragment_anna_debug(self, args: TaskConfig) -> list[DIOption]:
        ret = []
        c = args.addons.answerfile
        if c.ssh_installation_enabled:
            if c.answerfile_enable_networking is False:
                log_warn("SSH installation is enabled but networking is disabled!")
                log_warn("SSH installation only works with networking enabled!")
                log_warn("Proceeding without network debugging!")
                return []
            ret += [
                DIOption("#", "Anna / Debugging"),
            ]
            ret += []
            ret += [
                DIOption("anna/choose_modules", ["network-console"]),
                DIOption("user-setup/allow-password-weak", True),
                DIOption("network-console/password", c.ssh_installation_password),
                DIOption("network-console/password-again", c.ssh_installation_password),
            ]
        return ret

    def generate_fragment_locale(self, args: TaskConfig) -> list[DIOption]:
        c = args.addons.answerfile
        return [
            DIOption("#", "Locale"),
            DIOption("debian-installer/locale", c.locale_string),
            DIOption("localechooser/supported-locales", [c.locale_multi]),
            DIOption("keyboard-configuration/xkb-keymap", c.locale_keyboard, "select"),
        ]

    def generate_fragment_time(self, args: TaskConfig) -> list[DIOption]:
        c = args.addons.answerfile
        return [
            DIOption("#", "Time"),
            DIOption("clock-setup/utc", c.time_utc),
            DIOption("clock-setup/ntp", c.time_ntp),
            DIOption("time/zone", c.time_zone),
        ]

    def generate_fragment_users(self, args: TaskConfig) -> list[DIOption]:
        c = args.addons.answerfile
        result = []
        result += [
            DIOption("#", "Users (root)"),
            DIOption("passwd/root-login", c.user_root_enabled),
            DIOption("passwd/root-password", c.user_root_pw, "password"),
            DIOption("passwd/root-password-again", c.user_root_pw, "password"),
        ]

        result += [
            DIOption("#", "Users (OTHER)"),
            DIOption("passwd/make-user", c.user_other_enabled),
        ]
        if c.user_other_enabled:
            user = DEFAULT_USERNAME if c.user_other_name == "" else c.user_other_name
            pw = DEFAULT_PASSWORD if c.user_other_pw == "" else c.user_other_pw

            result += [
                DIOption("passwd/user-fullname", c.user_other_fullname),
                DIOption("passwd/username", user),
                DIOption("passwd/user-password", pw, "password"),
                DIOption("passwd/user-password-again", pw, "password"),
            ]
        return result

    def generate_fragment_mirrors(self) -> list[DIOption]:
        return [
            DIOption("#", "Mirrors"),
            DIOption("mirror/country", "manual"),
            DIOption("mirror/http/hostname", "httpredir.debian.org"),
            DIOption("mirror/http/directory", "/debian"),
            DIOption("mirror/http/proxy", ""),
        ]

    def generate_fragment_grub(self, args: TaskConfig) -> list[DIOption]:
        ret = []
        c = args.addons.answerfile
        fragment_name = "grub"
        if c.ssh_installation_breakpoint_pre.lower() == fragment_name:
            ret += self.generate_fragment_anna_debug(args)
        ret += [
            DIOption("#", "Grub"),
            DIOption("grub-installer/only_debian", True),
            DIOption("grub-installer/with_other_os", True),
            DIOption("grub-installer/update-nvram", True),
            DIOption("grub-installer/target", "x86_64-efi"),
            DIOption("grub-installer/efi_secure_boot", False),
            DIOption("grub-installer/choose_bootdev", "", "select"),
            DIOption("grub-installer/skip", False),
        ]
        if c.install_disk != "":
            ret.append(DIOption("grub-installer/bootdev", c.grub_install_device))
        else:
            ret.append(DIOption("grub-installer/bootdev", "select"))
        if c.ssh_installation_breakpoint_post.lower() == fragment_name:
            ret += self.generate_fragment_anna_debug(args)
        return ret

    def generate_fragment_packages(self, args: TaskConfig) -> list[DIOption]:
        ret = []
        c = args.addons.answerfile
        fragment_name = "packages"
        if c.ssh_installation_breakpoint_pre.lower() == fragment_name:
            ret += self.generate_fragment_anna_debug(args)
        ret += [
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
        ret += [
            DIOption("#", "Packages"),
            DIOption("tasksel/first", ["ssh-server"], "multiselect", "tasksel"),
            DIOption("pkgsel/upgrade", "full-upgrade"),
            DIOption("pkgsel/include", c.packages_install),
            DIOption("#", "Popularity Contest"),
            DIOption(
                "popularity-contest/participate", False, "boolean", "popularity-contest"
            ),
        ]
        if c.ssh_installation_breakpoint_post.lower() == fragment_name:
            ret += self.generate_fragment_anna_debug(args)
        return ret

    def generate_fragment_network(self, args: TaskConfig) -> list[DIOption]:
        ret = []
        c = args.addons.answerfile
        fragment_name = "network"
        if c.ssh_installation_breakpoint_pre.lower() == fragment_name:
            ret += self.generate_fragment_anna_debug(args)
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
                    DIOption("netcfg/get_ipaddress", c.net_ip),
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
        if c.ssh_installation_breakpoint_post.lower() == fragment_name:
            ret += self.generate_fragment_anna_debug(args)
        return ret

    def generate_fragment_hook_early(self, args: TaskConfig) -> list[DIOption]:
        ret = []
        cmdlist = self.create_hooks_early(args)
        if len(cmdlist) > 0:
            cmd_full = self.convert_tasklist(cmdlist)
            ret = [
                DIOption("#", "Hook (Early)"),
                DIOption("preseed/early_command", cmd_full),
            ]
        return ret

    def generate_fragment_hook_late(self, args: TaskConfig) -> list[DIOption]:
        cmdlist = self.create_hooks_late(args)
        cmd_full = self.convert_tasklist(cmdlist)
        return [
            DIOption("#", "Hook (Late)"),
            DIOption("preseed/late_command", cmd_full),
        ]

    def convert_tasklist(self, tasks: list[str]) -> str:
        i = 0
        result = f"{'':47}{LINE_CONT}"
        for task in tasks:
            line = f"{LINE_PREFIX}{task};"
            if i < len(tasks) - 1:
                line = f"{line:78} {LINE_CONT}"
            result = f"{result}{line}"
            i += 1
        return result

    def create_hooks_early(self, args: TaskConfig) -> list[str]:
        cmdlist = self.generate_early_commands_anna(args)
        cmdlist += self.generate_early_commands_debug(args)
        cmdlist += self.generate_early_commands_custom(args)
        return cmdlist

    def generate_early_commands_anna(self, args: TaskConfig) -> list[str]:
        udebs = " ".join(args.addons.answerfile.include_anna_packages)
        cmdlist = [
            "anna update",
            f"anna-install {udebs}",
        ]
        return cmdlist

    def generate_early_commands_debug(self, args: TaskConfig) -> list[str]:
        cmdlist = [
            # "db_fconsole --title 'Attention' --msg 'Please verify network configuration before first boot.'",
        ]
        return cmdlist

    def generate_early_commands_custom(self, args: TaskConfig) -> list[str]:
        cfg = args.addons.answerfile
        cmdlist = cfg.preseed_commands_early
        return cmdlist

    def create_hooks_late(self, args: TaskConfig) -> list[str]:
        cmdlist = self.generate_late_commands_users(args)
        cmdlist += self.generate_late_commands_copy_postinstaller(args)
        cmdlist += self.generate_late_commands_custom(args)
        return cmdlist

    def generate_late_commands_custom(self, args: TaskConfig) -> list[str]:
        cfg = args.addons.answerfile
        cmdlist = cfg.preseed_commands_late
        return cmdlist

    def generate_late_commands_users(self, args: TaskConfig) -> list[str]:
        cfg = args.addons.answerfile
        admin_group = cfg.admin_group_name
        config_group = cfg.config_group_name
        cmdlist = [f"in-target /usr/sbin/groupadd {admin_group}"]
        cmdlist += [f"in-target /usr/sbin/groupadd {config_group}"]
        if len(args.addons.answerfile.additional_users) > 0:
            for user in args.addons.answerfile.additional_users:
                cmdlist += [
                    f"in-target /sbin/adduser --disabled-password --gecos '' {user}"
                ]
        return cmdlist

    def generate_late_commands_copy_postinstaller(self, args: TaskConfig) -> list[str]:
        cfg = args.addons.answerfile
        cdrom_dir = cfg.answerfile_hook_dir_cdrom
        target_dir = cfg.answerfile_hook_dir_target
        filename = cfg.answerfile_hook_filename
        admin_group = cfg.admin_group_name
        cmdlist = [
            f"mkdir -p /target{target_dir}/",
            f"cp -r /cdrom{cdrom_dir}/* /target{target_dir}/",
        ]
        if args.addons.postinstall.postinstall_enabled:
            cmdlist += [
                f"in-target chown root:{admin_group} -R {target_dir}",
                f"in-target chmod 770 -R {target_dir}",
                "in-target chmod 770 /target/opt",
                f"in-target chmod 770 {target_dir}/{filename}",
                f"in-target /bin/bash {target_dir}/{filename}",
            ]
        return cmdlist

    def generate_fragment_partman(self, args: TaskConfig) -> list[DIOption]:
        ret = []
        c = args.addons.answerfile
        fragment_name = "network"
        if c.ssh_installation_breakpoint_pre.lower() == fragment_name:
            ret += self.generate_fragment_anna_debug(args)
        ret += [
            DIOption("#", "Partman"),
            DIOption("partman-partitioning/default_label", "gpt"),
            DIOption("partman-partitioning/choose_label", "gpt"),
            DIOption("partman-partitioning/confirm_write_new_label", True),
            DIOption("partman-lvm/device_remove_lvm", True),
            DIOption("partman-lvm/confirm", True),
            DIOption("partman-lvm/confirm_nooverwrite", True),
            DIOption("partman-md/device_remove_md", True),
        ]
        if c.install_disk != "":
            ret.append(DIOption("partman-auto/disk", c.install_disk, "string"))
        else:
            ret.append(DIOption("partman-auto/disk", "", "select"))

        if c.answerfile_enable_crypto:
            ret += [
                DIOption("#", "Partman (LUKS+LVM)"),
                DIOption("partman-auto/method", "crypto"),
                # DIOption("partman-auto/choose_recipe", "autocrypt-recipe", "select"),
                # DIOption("partman-auto/expert_recipe_file", "/autocrypt-recipe"),
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
                ret += [
                    DIOption("#", "Partman (LVM)"),
                    DIOption("partman-auto/method", "lvm"),
                    DIOption("partman-auto-lvm/guided_size", "max"),
                    DIOption("partman-auto-lvm/new_vg_name", c.disk_lvm_vg),
                    DIOption("partman-auto-lvm/choose_recipe", RECIPE_NAME, "select"),
                ]
            else:
                ret += [
                    DIOption("#", "Partman (Regular)"),
                    DIOption("partman-auto/method", "regular"),
                    DIOption("partman-auto/choose_recipe", RECIPE_NAME),
                ]

        ret += self.generate_fragment_recipe(args)
        ret += [
            DIOption("#", "Partman (Confirm)"),
            DIOption("partman/confirm", True),
            DIOption("partman/confirm_nooverwrite", True),
            DIOption("partman-partitioning/confirm_write_new_label", True),
        ]
        if c.answerfile_confirm_partitioning:
            ret += [
                DIOption("partman/confirm_write_new_label", True),
                DIOption("partman/choose_partition", "finish", "select"),
            ]
        if c.ssh_installation_breakpoint_post.lower() == fragment_name:
            ret += self.generate_fragment_anna_debug(args)

        return ret

    def generate_fragment_reboot(self, args: TaskConfig) -> list[DIOption]:
        result = []
        c = args.addons.answerfile
        if c.answerfile_confirm_final_reboot:
            result += [
                DIOption("#", "Confirm Reboot"),
                DIOption("finish-install/reboot_in_progress", "", "note"),
                DIOption("debian-installer/exit/reboot", True),
            ]
        return result

    def generate_fragment_recipe(self, args: TaskConfig) -> list[DIOption]:
        recipe = AnswerfileRecipe()
        disk_name = args.addons.answerfile.disk_lvm_vg
        recipe_name = args.addons.answerfile.disk_recipe
        recipe_custom = args.addons.answerfile.disk_recipe_custom
        disks = recipe.get_default_partitions(recipe_name, disk_name, recipe_custom)
        recipe = recipe.generate_recipe(RECIPE_NAME, disks)
        methods = "REGULAR"
        if args.addons.answerfile.answerfile_enable_crypto:
            methods = "LUKS+LVM"
        elif args.addons.answerfile.answerfile_enable_lvm:
            methods = "LVM"
        return [
            DIOption("#", f"Recipe ({methods})"),
            DIOption("partman-auto/expert_recipe", recipe),
        ]
