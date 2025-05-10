from unattend_my_iso.common.config import TaskConfig

LINE_PREFIX = "    "
LINE_CONT = "\\\n"


class AnswerfileCommands:

    def generate_fragment_hook_late(self, tasks: list[str]) -> str:
        i = 0
        result = f"{'':47}{LINE_CONT}"
        for task in tasks:
            line = f"{LINE_PREFIX}{task};"
            if i < len(tasks) - 1:
                line = f"{line:78} {LINE_CONT}"
            result = f"{result}{line}"
            i += 1
        return result

    def generate_default_hook_commands(self, args: TaskConfig) -> list[str]:
        result = []
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
        return result
