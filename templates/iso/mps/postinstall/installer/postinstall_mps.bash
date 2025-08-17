#!/bin/bash
# shellcheck disable=SC1090,1091
[[ -f /opt/umi/config/env.bash ]] && source /opt/umi/config/env.bash || exit 1

echo "-------------------------------------------------------------------------"
echo "- Unattend-My-Iso: POSTINSTALL MPS"
echo "-------------------------------------------------------------------------"
sleep 3

apt install -y ansible
cd "$CFG_ANSWERFILE_HOOK_DIR_TARGET"/repositories/mps || exit 1


ansible-playbook -i inventory/hosts playbooks/os.yml
ansible-playbook -i inventory/hosts playbooks/terminal.yml
ansible-playbook -i inventory/hosts playbooks/desktop.yml
ansible-playbook -i inventory/hosts playbooks/optimize.yml
ansible-playbook -i inventory/hosts playbooks/extras.yml


