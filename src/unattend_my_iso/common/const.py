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

# Logger
LOGGER = None
