import os
import pwd

# Globals
APP_VERSION = "0.0.9"

# Current user

user = os.environ["USER"]
if "SUDO_USER" in os.environ:
    user = os.environ["SUDO_USER"]
HOME = pwd.getpwnam(user).pw_dir
# HOME = os.path.expanduser("~")
USER = os.getlogin()

# Workspace search path
GLOBAL_WORKPATHS = ["/etc/umi", "/usr/share/umi",
                    f"{HOME}/.config/umi", os.getcwd()]

# Template
TEMPLATE_NAME = "desc.toml"
TEMPLATE_PREFIX = "desc."
TEMPLATE_SUFFIX = ".toml"

# Default args
DEFAULT_SUBNET = "10.10.123"
DEFAULT_NETMASK = "255.255.255.0"
DEFAULT_TIMEZONE = "EU/Berlin"
DEFAULT_LOCALE = "en_US"
DEFAULT_KEYBOARD = "de"
DEFAULT_HOSTNAME = "foo"
DEFAULT_DOMAIN = "local"
DEFAULT_DISK_RECIPE = "simple"
DEFAULT_VGNAME = "vg_main"
DEFAULT_USERNAME = "umi"
DEFAULT_USERNAME_ROOT = "root"
DEFAULT_PASSWORD_ROOT = "rootpass"
DEFAULT_PASSWORD_USER = "umipass"
DEFAULT_PASSWORD_CRYPTO = "diskpass"
DEFAULT_PASSWORD = "defaultpass"
DEFAULT_TEMPLATE = "mps"
DEFAULT_TEMPLATE_OVERLAY = "*"
DEFAULT_PASSWORD_LENGTH = 25
DEFAULT_PASSWORD_CHARSET = "A-Za-z0-9!&/=?+*#-_.:,;"

# liveboot
DIR_SQUASH = "squashfs"
NAME_SQUASH = "filesystem.squashfs"
TYPE_SQUASH = "squashfs"

# Logger
LOGGER = None

# ANSWERFILE
RECIPE_NAME = "custom-lvm"
LINE_PREFIX = "    "
LINE_LENGTH_MAX = 78
DOUBLE_PREFIX = f"{LINE_PREFIX}{LINE_PREFIX}"
TRIPLE_PREFIX = f"{DOUBLE_PREFIX}{LINE_PREFIX}"
LINE_CONT = " \\\n"
RECIPE_DISK_CONT = f"{DOUBLE_PREFIX}{'.':70}{LINE_CONT}"
RECIPE_DISK_END = f"{DOUBLE_PREFIX}.\n"

# Debugging
DEBUG_TEMPLATE = "mps"
DEBUG_OVERLAY = "live"
DEBUG_VERBOSITY = "2"
DEBUG_PROCTYPE = "addons"
DEBUG_WORKDIR = "."  # "/home/jb/mps/repo/gitlab/idris-iso-config"  # "."
DEBUG_WORKDIR_PREFIX = "../.."
DEFAULT_DEBUG_LEVEL = 4
