#!/bin/bash
#!/bin/bash

# Globals
export DEBIAN_FRONTEND=noninteractive
set -eo pipefail

# Install
apt install -y openssh-client openssh-server vim bind9-dnsutils tcpdump net-tools
