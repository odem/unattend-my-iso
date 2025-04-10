#!/bin/bash

# Environment variables
envfile=../config/env.bash
if [[ -f "$envfile" ]]; then
    # shellcheck disable=SC1090
    source "$envfile"
fi

export DEBIAN_FRONTEND=noninteractive
for file in /opt/umi/postinstall/* ; do 
    if [[ -f "$file" ]] ; then
        dpkg -i "$file"
    fi
done

