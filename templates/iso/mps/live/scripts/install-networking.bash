#!/bin/bash

echo "NET Installer"

apt-get update -y
apt-get install -f -y
apt-get upgrade -y
apt-get install -y openssh-server

