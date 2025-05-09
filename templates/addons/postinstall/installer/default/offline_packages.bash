#!/bin/bash

# Globals
export DEBIAN_FRONTEND=noninteractive

# shellcheck disable=SC1090,1091
[[ -f /opt/umi/config/env.bash ]] && source /opt/umi/config/env.bash || exit 1

echo "-------------------------------------------------------------------------"
echo "- Unattend-My-Iso: POSTINSTALL OFFLINE_PACKAGES"
echo "-------------------------------------------------------------------------"
sleep 1

# Install packages
UNMET_DEPS=0
for file in /opt/umi/packages/* ; do 
    if [[ -f "$file" ]] ; then
        echo -n "Installing deb package: $file ... "
        dpkg -i "$file" >/dev/null 2>/dev/null
        RET=$?
        if [[ $RET -eq 0 ]] ; then
            echo "Done!"
        else
            echo "Dependencies missing!"
            UNMET_DEPS=1
        fi
    fi
done
echo ""

# Inform user if needed
if [[ $UNMET_DEPS -eq 1 ]]; then
    echo "Offline packages might have unsatisfied dependencies"
    echo "Update with 'apt install -f' when package mirrors are available"
    echo ""
    sleep 3
fi

# Remove Job From Jobfile
echo "Sucessfully invoked all actions"
SERVICE=/firstboot.bash
if [[ -f "$SERVICE" ]]; then
    filename="$(basename "$0")"
    # shellcheck disable=SC2086
    sed s#$filename##g -i "$SERVICE"
    echo "Removed job from firstboot script: $(basename "$0")"
fi
echo ""
sleep 1
exit 0
