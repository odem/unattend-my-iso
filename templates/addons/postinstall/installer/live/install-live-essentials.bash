#!/bin/bash
#!/bin/bash

# Globals
export DEBIAN_FRONTEND=noninteractive
set -eo pipefail

# Install
apt install -y openssh-server vim netstat dnsutils tcpdump net-tools

