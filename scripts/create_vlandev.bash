#!/bin/bash

DEV=$1
TAG=$2
echo "Device: $DEV"
echo "VLAN  : $TAG"
ip link add link "$DEV" name "$DEV"."$TAG" type vlan id "$TAG"
ip link set dev "$DEV"."$TAG" up
ip addr add 10.10.127.1/24 dev "$DEV"."$TAG"
