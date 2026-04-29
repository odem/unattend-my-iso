#!/bin/bash

# Globals
export DEBIAN_FRONTEND=noninteractive
#set -eo pipefail
[[ -f /opt/umi/config/env.bash ]] && source /opt/umi/config/env.bash || exit 1

# Defaults
USERNAME="$CFG_LIVE_BOOT_USERNAME"
USERDIR="/home/$USERNAME"
SSHDIR="$USERDIR/.ssh"
[[ "$USERNAME" == "" ]] && exit 0
# Install
if ! id "$USERNAME" 2>/dev/null; then
  adduser --disabled-password --gecos '' "$USERNAME"
fi
if ! id "$USERNAME" 2>/dev/null; then
  adduser --disabled-password --gecos '' "$USERNAME"
  echo "$USERNAME:${USERNAME}pass" | chpasswd
fi

echo "$USERNAME:${USERNAME}pass" | chpasswd
mkdir -p "$SSHDIR"
chown "$USERNAME":"$USERNAME" -R "$USERDIR"
chmod 0600 "$SSHDIR"/*

# Configure default user
if [[ "$USERNAME" != "" ]]; then
  echo "-> Prepare default user '$USERNAME'"
  if [[ -d "$CFG_ANSWERFILE_HOOK_DIR_TARGET/users/$USERNAME/" ]]; then
    cp -r "$CFG_ANSWERFILE_HOOK_DIR_TARGET/users/$USERNAME/". "/home/$USERNAME"
    cp -r "$CFG_ANSWERFILE_HOOK_DIR_TARGET/users/$USERNAME/". "/root/"
  fi
  if [[ -f "$CFG_ANSWERFILE_HOOK_DIR_TARGET/ssh/authorized_keys" ]]; then
    cat "$CFG_ANSWERFILE_HOOK_DIR_TARGET/ssh/authorized_keys" \
      >"/home/$USERNAME"/.ssh/authorized_keys
    cat "$CFG_ANSWERFILE_HOOK_DIR_TARGET/ssh/authorized_keys" \
      >/root/.ssh/authorized_keys
  fi
  chmod 700 -R "/home/$USERNAME/"
  chown "$USERNAME:$USERNAME" -R "/home/$USERNAME/"
fi

cat "$CFG_ANSWERFILE_HOOK_DIR_TARGET"/config/.bash_aliases >/etc/bash_aliases
chmod 644 "/root/.bash"*
chmod 644 /etc/bash_aliases
