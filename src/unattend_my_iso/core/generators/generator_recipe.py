from unattend_my_iso.common.model import PartitionFlag, RecipeDescription
from unattend_my_iso.common.const import (
    DOUBLE_PREFIX,
    LINE_CONT,
    LINE_LENGTH_MAX,
    LINE_PREFIX,
    RECIPE_DISK_CONT,
    RECIPE_DISK_END,
    TRIPLE_PREFIX,
)


class AnswerfileRecipe:

    def generate_recipe(self, name: str, disks: list[RecipeDescription]) -> str:
        i = 0
        body = ""
        recipe_head = self.create_recipe_head(name)
        for disk in disks:
            fragment = self.create_partition_fragment(disk)
            if fragment != "":
                if i < len(disks) - 1:
                    body += f"{fragment:78}{RECIPE_DISK_CONT}"
                else:
                    body += f"{fragment:78}{RECIPE_DISK_END}"
            i += 1
        result = f"{recipe_head}{body}"
        return result

    def create_recipe_head(self, name: str) -> str:
        text = f"{LINE_PREFIX}{name} ::"
        return f"{'':40}{LINE_CONT}{text:78}{LINE_CONT}"

    def get_default_partitions(self, vg_name: str):
        # wiese
        return [
            RecipeDescription([1024], "vfat", "/boot/efi", "", "", "ESP", "gpt"),
            RecipeDescription([1024], "ext4", "/boot", "", "", "BOOT", "gpt"),
            RecipeDescription([4096], "linux-swap", "", "", "", "SWAP", "gpt"),
            RecipeDescription([50000, 50000, 50000], "ext4", "/", vg_name, "lv_root"),
        ]

        # mps
        # return [
        #     RecipeDescription([1024], "vfat", "/boot/efi", "", "", "ESP", "gpt"),
        #     RecipeDescription([1024], "ext4", "/boot", "", "", "BOOT", "gpt"),
        #     RecipeDescription([4096], "linux-swap", "", vg_name, "lv_swap"),
        #     RecipeDescription([50000, 50000, 50000], "ext4", "/", vg_name, "lv_root"),
        #     RecipeDescription(
        #         [100000, 100000, 100000], "ext4", "/srv", vg_name, "lv_srv"
        #     ),
        #     RecipeDescription(
        #         [1400000, 1400000, 1400000], "ext4", "/home", vg_name, "lv_home"
        #     ),
        #     RecipeDescription([10000, 100000, 100000], "ext4", "/media/disks/extra"),
        # ]

    def create_partition_fragment(self, desc: RecipeDescription) -> str:
        body = ""
        result = ""
        line = TRIPLE_PREFIX
        header = self.create_partition_header(desc)
        flags = self.create_partition_flags(desc)
        for flag in flags:
            flagstr = flag.__str__()
            if len(line) + len(flagstr) + 1 < LINE_LENGTH_MAX - 1:
                line += f"{flagstr} "
            else:
                body += f"{line:78}{LINE_CONT}"
                line = f"{TRIPLE_PREFIX}{flagstr} "
        body += f"{line:78}{LINE_CONT}"
        result = f"{header:78}{LINE_CONT}{body:78}"
        return result

    def create_partition_header(self, desc: RecipeDescription) -> str:
        result = DOUBLE_PREFIX
        iterate = desc.sizes.copy()
        if len(desc.sizes) == 1:
            iterate.append(desc.sizes[0])
            iterate.append(desc.sizes[0])
        elif len(desc.sizes) == 2:
            iterate.insert(0, desc.sizes[0])
        for size in iterate:
            result = f"{result}{size} "
        result = f"{result}{desc.use_type} "
        return result

    def create_partition_flags(self, desc: RecipeDescription) -> list[PartitionFlag]:
        result = []
        self.append_options_lvm(result, desc)
        self.append_options_primary(result, desc)
        self.append_options_method(result, desc)
        self.append_options_fs(result, desc)
        return result

    def append_options_primary(
        self, arr: list[PartitionFlag], desc: RecipeDescription
    ) -> list[PartitionFlag]:
        if desc.mountpoint == "/boot/efi":
            arr += [
                PartitionFlag("label", desc.label),
                PartitionFlag("$iflabel", desc.iflabel),
                PartitionFlag("bootflag", "ef"),
            ]
        elif desc.mountpoint == "/boot":
            arr += [
                PartitionFlag("label", desc.label),
                PartitionFlag("$iflabel", desc.iflabel),
                PartitionFlag("bootable"),
            ]
        return arr

    def append_options_method(
        self, arr: list[PartitionFlag], desc: RecipeDescription
    ) -> list[PartitionFlag]:
        method = "format"
        if desc.use_type == "linux-swap":
            method = "swap"
        elif desc.mountpoint == "/boot/efi":
            method = "efi"
        arr += [
            PartitionFlag("method", method),
            PartitionFlag("format"),
        ]
        return arr

    def append_options_lvm(
        self, arr: list[PartitionFlag], desc: RecipeDescription
    ) -> list[PartitionFlag]:
        if desc.name_lv != "" and desc.name_vg != "":
            arr += [
                PartitionFlag("$lvmok"),
                PartitionFlag("lv_name", desc.name_lv),
                PartitionFlag("in_vg ", desc.name_vg),  # CAUTION: Needs trailing space!
            ]
        else:
            arr += [PartitionFlag("$primary")]
        return arr

    def append_options_fs(
        self, arr: list[PartitionFlag], desc: RecipeDescription
    ) -> list[PartitionFlag]:
        if desc.mountpoint != "" and desc.use_type != "":
            arr += [
                PartitionFlag("use_filesystem"),
                PartitionFlag("filesystem", desc.use_type),
                PartitionFlag("mountpoint", desc.mountpoint),
            ]
        return arr
