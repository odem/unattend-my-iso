#!/bin/bash

# Globals
export DEBIAN_FRONTEND=noninteractive
#set -e

# shellcheck disable=SC1090,1091
[[ -f /opt/umi/config/env.bash ]] && source /opt/umi/config/env.bash || exit 1

SRCDIR="$CFG_ANSWERFILE_HOOK_DIR_TARGET"/postinstall/cronjobs
DSTDIR="/home/$CFG_USER_OTHER_NAME/cronjobs"

echo "-------------------------------------------------------------------------"
echo "- Unattend-My-Iso: POSTINSTALL CRONJOBS"
echo "-------------------------------------------------------------------------"
echo ""
sleep 1
CRONSCHEDULE="$DEFAULT_CRON_SCHEDULE"
CRONARGS="$DEFAULT_CRON_ARGS"

# Cron config
if [[ -d "$SRCDIR" ]] ; then
    for f in "$SRCDIR"/*; do
        echo "Configuring $f"
        DSTFILE="$DSTDIR/"$(basename "$f")
        DSTDIR=$(dirname "$DSTFILE")
        mkdir -p "$DSTDIR"
        cp "$f" "$DSTFILE"
        chmod +x "$DSTFILE"
        chown "$CFG_USER_OTHER_NAME":"$CFG_USER_OTHER_NAME" "$DSTFILE"
        job="$CRONSCHEDULE $DSTFILE $CRONARGS  2>&1 >>$DSTDIR/cron"
        CONFIGURED=$(crontab -u "$CFG_USER_OTHER_NAME" -l | grep -F "$DSTFILE")
        if [ "$CONFIGURED" == "" ]; then
            (echo "$job") | crontab  -u "$CFG_USER_OTHER_NAME" -
            echo "Cron job add: $DSTFILE"
        fi
    done
fi
exit 0
