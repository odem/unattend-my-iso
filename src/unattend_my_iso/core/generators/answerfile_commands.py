from unattend_my_iso.common.config import TaskConfig, TemplateConfig

LINE_PREFIX = "    "
LINE_CONT = "\\\n"


class AnswerfileCommands:

    def generate_fragment_hook_late(
        self, tasks: list[str], args: TaskConfig, template: TemplateConfig
    ) -> str:
        i = 0
        result = f"{'':47}{LINE_CONT}"
        for task in tasks:
            line = f"{LINE_PREFIX}{task};"
            if i < len(tasks) - 1:
                line = f"{line:78} {LINE_CONT}"
            result = f"{result}{line}"
            i += 1
        return result
