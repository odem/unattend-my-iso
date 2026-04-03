#!/bin/bash

DEV=$1
FILE=$2
echo "Device: $DEV"
echo "File  : $FILE"

sudo killall dnsmasq
sudo dnsmasq -C "$FILE"
sudo tail -f /var/log/dnsmasq.log
