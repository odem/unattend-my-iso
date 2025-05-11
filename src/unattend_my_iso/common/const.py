import os

# Template
TEMPLATE_NAME = "desc.toml"
TEMPLATE_PREFIX = "desc."
TEMPLATE_SUFFIX = ".toml"

# Globals
APP_VERSION = "0.0.2"
DEFAULT_TEMPLATE = "mps"
DEFAULT_TEMPLATE_OVERLAY = "*"

# Default args
HOMEDIR = os.path.expanduser("~")
USER = os.getlogin()
DEFAULT_SUBNET = "10.10.123"
DEFAULT_TIMEZONE = "EU/Berlin"
DEFAULT_LOCALE = "en_US"
DEFAULT_KEYBOARD = "de"
DEFAULT_HOSTNAME = "foo"
DEFAULT_DOMAIN = "local"
DEFAULT_VGNAME = "vg_main"
DEFAULT_USERNAME = "umi"
DEFAULT_PASSWORD_ROOT = "rootpass"
DEFAULT_PASSWORD_USER = "umipass"
DEFAULT_PASSWORD_CRYPTO = "diskpass"
DEFAULT_PASSWORD = "otherpass123"

# Processor
GLOBAL_WORKPATHS = ["/etc/umi", "/usr/share/umi", f"{HOMEDIR}/.config/umi"]

# Logger
LOGGER = None

# ANSWERFILE
RECIPE_NAME = "custom-lvm"

# Answerfile Recipe
LINE_PREFIX = "    "
LINE_LENGTH_MAX = 78
DOUBLE_PREFIX = f"{LINE_PREFIX}{LINE_PREFIX}"
TRIPLE_PREFIX = f"{DOUBLE_PREFIX}{LINE_PREFIX}"
LINE_CONT = " \\\n"
RECIPE_DISK_CONT = f"{DOUBLE_PREFIX}{'.':70}{LINE_CONT}"
RECIPE_DISK_END = f"{DOUBLE_PREFIX}.\n"

# Debugging
DEBUG_TEMPLATE = "proxmox"
DEBUG_OVERLAY = "*"
DEBUG_VERBOSITY = "3"
DEBUG_PROCTYPE = "net_start"
