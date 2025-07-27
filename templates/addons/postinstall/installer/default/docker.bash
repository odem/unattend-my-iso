#!/bin/bash

# Globals
export DEBIAN_FRONTEND=noninteractive
set -e

# shellcheck disable=SC1090,1091
[[ -f /opt/umi/config/env.bash ]] && source /opt/umi/config/env.bash || exit 1

echo "-------------------------------------------------------------------------"
echo "- Unattend-My-Iso: POSTINSTALL DOCKER"
echo "-------------------------------------------------------------------------"
echo ""
sleep 1

# Install defaults
apt-get -y update && apt-get -y upgrade
apt-get -y install ca-certificates curl
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg \
    -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

KEY_ASC="/etc/apt/keyrings/docker.asc"
DOCKER_REPO="https://download.docker.com/linux/debian"
# shellcheck disable=SC1090,1091
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=$KEY_ASC] $DOCKER_REPO \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get -y update
apt-get -y install \
    docker-ce \
    docker-ce-cli \
    containerd.io \
    docker-buildx-plugin \
    docker-compose-plugin
apt-get -y autoremove

# Define overlay folder
cat <<EOF > /etc/docker/daemon.json
{
  "data-root": "$DOCKER_ROOT/overlays"
}
EOF
mkdir -p "$DOCKER_ROOT/volumes"
mkdir -p "$DOCKER_ROOT/overlays"
chown -R "root:docker" "$DOCKER_ROOT"
systemctl restart docker

# Configure admin users
for i in $(seq 0 $(("${#CFG_ADMIN_USERS[*]}" - 1))); do
    ADMIN_NAME="${CFG_ADMIN_USERS[$i]}"
    echo "-> Prepare docker user '$ADMIN_NAME'"
    /sbin/usermod -aG "$CFG_ADMIN_GROUP_NAME" "$ADMIN_NAME"
done

# Remove Job From Jobfile
echo "Sucessfully invoked all actions"
SERVICE=/firstboot.bash
if [[ -f "$SERVICE" ]]; then
    filename="$(basename "$0")"
    # shellcheck disable=SC2086
    sed -i "/$filename/d" "$SERVICE"
    echo "Removed job from firstboot script: $(basename "$0")"
fi
echo ""
sleep 1
exit 0
