#!/bin/bash

# shellcheck disable=SC2115

# Globals
export DEBIAN_FRONTEND=noninteractive
set -e

# shellcheck disable=SC1090,1091
[[ -f /opt/umi/config/env.bash ]] && source /opt/umi/config/env.bash || exit 1

# Install db client
apt install -y ansible

# guacweb: Prepare lockdown repo
CISREPO="$CFG_ANSWERFILE_HOOK_DIR_TARGET"/repositories/DEBIAN12-CIS
LOCKDOWN_CONF_DIR="$CFG_ANSWERFILE_HOOK_DIR_TARGET"/postinstall/lockdown


cp -r "$LOCKDOWN_CONF_DIR"/* "$CISREPO"/
chown root:"$CFG_ADMIN_GROUP_NAME" -R "$CISREPO"

cd "$CISREPO" || exit 1

if [[ ! -f ~/.ssh/id_rsa ]] ; then
    ssh-keygen -t rsa -b 4096
    ssh-copy-id deploy@localhost
fi
ansible-playbook -i inventory/hosts site.yml

# Adjust permissions
exit 0

