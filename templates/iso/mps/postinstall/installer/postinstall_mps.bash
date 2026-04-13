#!/bin/bash
# shellcheck disable=SC1090,1091
[[ -f /opt/umi/config/env.bash ]] && source /opt/umi/config/env.bash || exit 1

echo "-------------------------------------------------------------------------"
echo "- Unattend-My-Iso: POSTINSTALL MPS"
echo "-------------------------------------------------------------------------"
sleep 3

REPODIR="$CFG_ANSWERFILE_HOOK_DIR_TARGET"/repositories/ansible-fragments
cd "$REPODIR" || exit 1

# Install
sudo apt install -y ansible

# Create inventory
cp inventory/hosts_local inventory/hosts
sudo chown "$USER:$USER" inventory/hosts

# run
export ANSIBLE_NOWCOWS=1
ansible-playbook playbooks/baseos.yml
ansible-playbook playbooks/usermanager.yml
ansible-playbook playbooks/installer-terminal.yml
ansible-playbook playbooks/installer-services.yml
