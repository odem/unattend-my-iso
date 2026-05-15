from unattend_my_iso.common.logging import log_info
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

1GBSIZE = [1024]
2GBSIZE = [2048]
4GBSIZE = [4096]
BNAME = "/boot/efi"
ENAME = "/media/disks/extra"


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

    def create_partition_layout_custom(self, definitions: list):
        return [RecipeDescription(*x) for x in definitions]

    def create_partition_layout_simple(self, vg_name: str):
        mainsize = [40000, 45000, "100%"]
        return [
            RecipeDescription(1GBSIZE, "vfat", BNAME, "", "", "ESP", "gpt"),
            RecipeDescription(1GBSIZE, "ext4", "/boot", "", "", "BOOT", "gpt"),
            RecipeDescription(4GBSIZE, "linux-swap", "", vg_name, "lv_swap"),
            RecipeDescription(mainsize, "ext4", "/", vg_name, "lv_root"),
        ]

    def create_partition_layout_extrapart(self, vg_name: str):
        mainsize = [30000, 35000, 35000]
        extrasize = [10000, 10000, "100%"]
        return [
            RecipeDescription(1GBSIZE, "vfat", BNAME, "", "", "ESP", "gpt"),
            RecipeDescription(1GBSIZE, "ext4", "/boot", "", "", "BOOT", "gpt"),
            RecipeDescription(4GBSIZE, "linux-swap", "", vg_name, "lv_swap"),
            RecipeDescription(mainsize, "ext4", "/", vg_name, "lv_root"),
            RecipeDescription(extrasize, "ext4", ENAME),
        ]

    def create_partition_layout_mps(self, vg_name: str):
        mainsize = [50000, 50000, 100000]
        extrasize = [10000, 10000, 10000]
        homesize = [5000, 5000, 50000]
        srvsize = [1000, 10000, 100000]
        return [
            RecipeDescription(1GBSIZE, "vfat", BNAME, "", "", "ESP", "gpt"),
            RecipeDescription(1GBSIZE, "ext4", "/boot", "", "", "BOOT", "gpt"),
            RecipeDescription(extrasize, "ext4", ENAME),
            RecipeDescription(4GBSIZE, "linux-swap", "", vg_name, "lv_swap"),
            RecipeDescription(mainsize, "ext4", "/", vg_name, "lv_root"),
            RecipeDescription(homesize, "ext4", "/home", vg_name, "lv_home"),
            RecipeDescription(srvsize, "ext4", "/srv", vg_name, "lv_srv"),
        ]

    def get_default_partitions(self, method: str, vg_name: str, definitions: list):
        log_info(f"Using template:  {method}", self.__class__.__qualname__)
        if method == "mps":
            return self.create_partition_layout_mps(vg_name)
        elif method == "simple":
            return self.create_partition_layout_simple(vg_name)
        elif method == "extrapart":
            return self.create_partition_layout_extrapart(vg_name)
        elif method == "custom":
            return self.create_partition_layout_custom(definitions)
        else:
            return self.create_partition_layout_simple(vg_name)

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
                PartitionFlag("bootflag", "efi"),
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
                # CAUTION: Needs trailing space!
                PartitionFlag("in_vg ", desc.name_vg),
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
