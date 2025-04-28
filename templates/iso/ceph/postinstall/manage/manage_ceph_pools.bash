#!/bin/bash

# shellcheck disable=SC1090,1091
[[ -f /opt/umi/config/env.bash ]] && source /opt/umi/config/env.bash || exit 1

MONITOR_LIST="$NODES_CEPH_MANAGE_NAME"
SLEEPTIME=3
TEST_POOL_RBDREP=repblock
TEST_POOL_RBDEC=ecblock
TEST_POOL_CFSREP=repfiles
TEST_POOL_CFSEC=ecfiles
AUTOSACALER_LEVEL="off"
POOL_BULK="true"
POOL_EC_OVERWRITES="true"
PG_AMOUNT=16
NAME_PREFIX="nhc"
NAME_SUFFIX_CFS="fs"
NAME_PREFIX_PROFILE="cit"
ENTITY_NAME=""
REP_SIZE=""
BUCKET_CLASS=""
BUCKET_TYPE=""
BUCKET_LOCATION=""
ENTITY_LIST=""

# ceph osd pool create cachepool 64
# ceph osd tier add myecpool cachepool
# ceph osd tier cache-mode cachepool writeback
# ceph osd tier set-overlay myecpool cachepool

# -----------------------------------------------------------------------------
# Single Targets
# -----------------------------------------------------------------------------

usage() {
    echo "      "
    echo "Usage: $0 -a ACTION [PARAMS] [FLAGS]"
    echo "      "
    echo "    Parameters:"
    echo "      -a action_name       : Name of the action to execute"
    echo "      -n entity_name       : Name of the entity"
    echo "      -N entity_list       : List of the entities"
    echo "      -R entity_related    : Name of the related entity"
    echo "      -r replicated_size   : Size of the replica (int)"
    echo "      -k data_chunks       : Amount of data chunks (int)"
    echo "      -m coding_chunks     : Amount of coding chunks (int)"
    echo "      -p pg_count          : Amount of placement groups (int)"
    echo "      -s autoscale_level   : on, off or warn"
    echo "      -b bulk              : true or false (default: true)"
    echo "      -o ec_overwrites     : true or false (default: true)"
    echo "      -t bucket_type       : Crush bucket type (e.g. datacenter,host,etc.)"
    echo "      -c bucket_class      : Crush bucket class (default: '', hdd or ssd)"
    echo "      -l bucket_location   : Crush bucket location (Optional! e.g. root=default)"
    echo "      "
    echo "    Flags:"
    echo "      -h                 : Print usage and exit"
    echo "      "
    echo "    Actions:"
    echo "      init-cluster             : Bootstrap new cluster"
    echo "      add-bucket               : add crush bucket"
    echo "      del-bucket               : delete crush bucket"
    echo "      move-bucket              : move crush bucket to location"
    echo "      add-ec-rule              : add ec rule"
    echo "      del-ec-rule              : delete ec rule"
    echo "      add-ec-profile           : add ec profile"
    echo "      del-ec-profile           : delete ec profile"
    echo "      add-rbd-ec               : Create ec rbd pool (implies -k and -m)"
    echo "      del-rbd-ec               : Create ec rbd pool (implies -k and -m)"
    echo "      add-rbd-rep              : Create replicated rbd pool (implies -r)"
    echo "      del-rbd-rep              : Create replicated rbd pool (implies -r)"
    echo "      del-rbd-forced           : delete rbd pool by raw name"
    echo "      add-fs-ec                : Create ec fs (implies -k and -m)"
    echo "      del-fs-ec                : Create ec fs (implies -k and -m)"
    echo "      del-fs-forced            : delete filesystem by raw name"
    echo "      add-fs-rep               : Create replicated fs (implies -r)"
    echo "      del-fs-rep               : Create replicated fs (implies -r)"
    echo "      mount-fs                 : Mount fs (implies -r or (-k and -m))"
    echo "      unmount-fs               : Unmount fs (implies -r or (-k and -m))"
    echo "      "
    echo "    Group Actions:"
    echo "      bootstrap-cluster        : init with dashboard, hosts, disks and crush"
    echo "      create-dashboard         : Enable dashboard module"
    echo "      enforce-bucket-root      : Forces all hosts to root bucket"
    echo "      enforce-bucket-locations : Forces all hosts to correct location"
    echo "      add-all-hosts            : add all hosts"
    echo "      add-all-disks            : add all disks"
    echo "      add-all-buckets          : add crush bucket"
    echo "      del-all-buckets          : delete crush bucket"
    echo "      add-all-profiles         : add all profiles"
    echo "      del-all-profiles         : delete all profiles"
    echo "      add-all-fs               : create all filesystems with pools"
    echo "      del-all-fs               : delete all filesystems with pools"
    echo "      mount-all-fs             : mount all filesystems"
    echo "      unmount-all-fs           : unmount all filesystems"
    echo "      add-all-pools            : add all rbd pools"
    echo "      del-all-pools            : delete all rbd pools"
    echo "      recreate-all-pools       : delete all pools and fs, then readd"
    echo "      add-all-crush            : delete all crush rules"
    echo "      del-all-crush            : delete all crush rules"
    echo "      recreate-all-crush       : delete all profiles, buckets and rules, then read"
    echo "      create-all               : bootstrap, create-buckets then create-pools"
    echo "      "
    echo "    Status Actions:"
    echo "      status-cluster           : Collect status messages for cluster"
    echo "      status-storage           : Collect status messages for storage"
    echo "      "
}
read_nodes_from_config() {
    if [[ "$NODES_CEPH_MANAGE_NAME" != "" ]]; then
        IFS=',' read -ra MEMBERS_CEPH_MANAGE_NAME <<< "$NODES_CEPH_MANAGE_NAME"
        LINE="${#MEMBERS_CEPH_MANAGE_NAME[*]} configured cluster Members: ${MEMBERS_CEPH_MANAGE_NAME[*]}"
        [[ $VERBOSE -eq 1 ]] && echo "$LINE"
    fi
}
read_entitylist() {
    if [[ "$ENTITY_LIST" != "" ]]; then
        IFS=',' read -ra PARSED_ENTITIES <<< "$ENTITY_LIST"
        LINE="${#PARSED_ENTITIES[*]} parsed entities: ${PARSED_ENTITIES[*]}"
        [[ $VERBOSE -eq 1 ]] && echo "$LINE"
    fi
}
ping_hosts() {
    echo "--- Ping Hosts -----------------------------------------------"
    for i in $(seq 0 $(("${#MEMBERS_CEPH_MANAGE_NAME[*]}" - 1))); do
        item="${MEMBERS_CEPH_MANAGE_NAME[$i]}"
        echo "Pinging $item ..."
        ping -c 1 "$item"
    done
}
init_cluster() {
    ping_hosts
    echo "--- Bootstrap Cluster ----------------------------------------"
    sudo cephadm bootstrap \
        --mon-ip "$STORAGE_IP" \
        --cluster-network "$STORAGE_NET.0/24"
}
create_dashboard() {
    echo "--- Configure Dashboard --------------------------------------"
    sudo ceph telemetry on --license sharing-1-0
    ceph telemetry enable channel perf
    echo "$CEPH_UI_PASSWORD" > ./pw.txt
    # Need for hyper-converged dashboard:
    # ceph dashboard ac-user-create bofh -i ./pw.txt administrator
    sudo ceph dashboard ac-user-set-password admin -i ./pw.txt
    sudo rm -rf pw.txt
}
enable_app() {
    APPNAME=$1
    APP=$2
    ceph osd pool application enable "$APPNAME" "$APP" --yes-i-really-mean-it 
}
add_bucket() {
    B_NAME="${1}"
    B_TYPE="${2}"
    B_LOCATION="${3}"
    del_bucket "$B_NAME"
    echo "--- Create CRUSH Rule ----------------------------------------"
    echo "Creating crush rule: $B_NAME (Location: $B_LOCATION)"
    # shellcheck disable=SC2086
    ceph osd crush add-bucket "$B_NAME" "$B_TYPE" $B_LOCATION # Do not quote location!

}
del_bucket() {
    echo "--- Delete CRUSH Rule ----------------------------------------"
    BUCKET_NAME_RM="${1}"
    HAS_BUCKET=$(ceph osd crush dump | jq ".buckets[].name" | grep -c "$BUCKET_NAME_RM" )
    echo "Deleting bucket    : '$BUCKET_NAME_RM' $HAS_BUCKET"
    [[ $HAS_BUCKET -gt 0 ]] || return 0
    ceph osd crush remove "$BUCKET_NAME_RM"
}
move_bucket() {
    MOVEB_NAME="${1}"
    MOVEB_LOCATION="${2}"
    echo "--- Move CRUSH Bucket ----------------------------------------"
    echo "Moving crush bucket: $MOVEB_NAME (Location: $MOVEB_LOCATION)"
    # shellcheck disable=SC2086
    ceph osd crush move "$MOVEB_NAME" $MOVEB_LOCATION # Do not quote location!
}
add_ec_rule() {
    CRUSH_RULE="${1}"
    POOL_PROFILE="${2}"
    del_ec_rule "$CRUSH_RULE"
    echo "--- Create CRUSH Rule ----------------------------------------"
    echo "Creating crush rule: $CRUSH_RULE"
    ceph osd crush rule create-erasure "$CRUSH_RULE" "$POOL_PROFILE"
}
del_ec_rule() {
    echo "--- Delete CRUSH Rule ----------------------------------------"
    CRUSH_RULE_RM="${1}"
    HAS_RULE=$(ceph osd crush rule ls | grep -c "$CRUSH_RULE_RM" )
    echo "Deleting crush rule: $CRUSH_RULE_RM"
    [[ $HAS_RULE -gt 0 ]] || return 0
    ceph osd crush rule rm "$CRUSH_RULE_RM"
}
add_rep_rule() {
    REPBUCKET_NAME="${1}"
    REPBUCKET_ROOT="${2}"
    REPBUCKET_TYPE="${3}"
    REPBUCKET_CLASS="${4}"
    del_rep_rule "$REPBUCKET_NAME"
    echo "--- Create CRUSH Rule ----------------------------------------"
    echo "Creating crush rule: $REPBUCKET_NAME"
    ceph osd crush rule create-replicated "$REPBUCKET_NAME" "$REPBUCKET_ROOT" \
        "$REPBUCKET_TYPE" "$REPBUCKET_CLASS"
}
del_rep_rule() {
    echo "--- Delete CRUSH Rule (REP) ----------------------------------"
    CRUSH_RULE_REPRM="${1}"
    HAS_RULE=$(ceph osd crush rule ls | grep -c "$CRUSH_RULE_REPRM" )
    echo "Deleting crush rule: $CRUSH_RULE_REPRM"
    [[ $HAS_RULE -gt 0 ]] || return 0
    ceph osd crush rule rm "$CRUSH_RULE_REPRM"
}
add_ec_profile() {
    echo "--- Create EC-Profile ----------------------------------------"
    PROFILE_NAME="${1}k${2}m${3}"
    echo "Creating ec profile: $PROFILE_NAME"
    ceph osd erasure-code-profile set "$PROFILE_NAME" "k=$2" "m=$3" \
        crush-failure-domain="$4"
}
del_ec_profile() {
    echo "--- Delete EC-Profile ----------------------------------------"
    PROFILE_NAME="${1}k${2}m${3}"
    echo "Deleting ec profile: $PROFILE_NAME"
    ceph osd erasure-code-profile rm "$PROFILE_NAME"
}
add_rbd_ec() {
    echo "--- Add Pool (EC) --------------------------------------------"
    ADDEC_NAME=$1
    RULE="k${3}m${4}"
    APP=$5
    ADDEC_POOL_NAME="$NAME_PREFIX-$ADDEC_NAME-$RULE"
    PROFILE="cit$RULE"
    HAS_POOL=$(ceph osd pool ls | grep -c "$ADDEC_POOL_NAME")
    if [[ $HAS_POOL -eq 0 ]]; then
        echo "Create ec pool $ADDEC_POOL_NAME -> $PROFILE"
        ceph osd pool create "$ADDEC_POOL_NAME" \
            "$PG_AMOUNT" "$PG_AMOUNT" erasure "$PROFILE"
        ceph osd pool set "$ADDEC_POOL_NAME" allow_ec_overwrites "$POOL_EC_OVERWRITES"
        ceph osd pool set "$ADDEC_POOL_NAME" bulk "$POOL_BULK"
        ceph osd pool set "$ADDEC_POOL_NAME" pg_autoscale_mode "$AUTOSACALER_LEVEL"
        if [[ "$APP" != "" ]]; then
            rbd pool init "$ADDEC_POOL_NAME"
            enable_app "$ADDEC_POOL_NAME" "rados"
            enable_app "$ADDEC_POOL_NAME" "rbd"
        fi
    else
        echo "The specified rbd pool already exists: $ADDEC_POOL_NAME"
    fi
}
del_rbd_ec() {
    echo "--- Del Pool (EC) --------------------------------------------"
    DELEC_NAME=$1
    RULE="k${3}m${4}"
    DELEC_POOL_NAME="$NAME_PREFIX-$DELEC_NAME-$RULE"
    PROFILE="cit$RULE"
    HAS_POOL=$(ceph osd pool ls | grep -c "$DELEC_POOL_NAME")
    if [[ $HAS_POOL -gt 0 ]]; then
        echo "Delete ec pool $DELEC_POOL_NAME -> $PROFILE"
        allow_pool_delete
        ceph osd pool rm "$DELEC_POOL_NAME" "$DELEC_POOL_NAME" \
            --yes-i-really-really-mean-it
        deny_pool_delete
    else
        echo "The specified rbd pool does not exist: $DELEC_POOL_NAME"
    fi
}
add_rbd_rep() {
    echo "--- Add Pool (REP) -------------------------------------------"
    ADDREP_NAME=$1
    RULE="rep${3}"
    APP=$4
    ADDREP_POOL_NAME="$NAME_PREFIX-$ADDREP_NAME-$RULE"
    HAS_POOL=$(ceph osd pool ls | grep -c "$ADDREP_POOL_NAME")
    if [[ $HAS_POOL -eq 0 ]]; then
        echo "Create replicated pool $ADDREP_POOL_NAME -> $RULE"
        ceph osd pool create "$ADDREP_POOL_NAME" \
            "$PG_AMOUNT" "$PG_AMOUNT" replicated
        ceph osd pool set "$ADDREP_POOL_NAME" size "$3"
        ceph osd pool set "$ADDREP_POOL_NAME" bulk "$POOL_BULK"
        ceph osd pool set "$ADDREP_POOL_NAME" pg_autoscale_mode "$AUTOSACALER_LEVEL"
        if [[ "$APP" != "" ]]; then
            rbd pool init "$ADDREP_POOL_NAME"
            enable_app "$ADDREP_POOL_NAME" "rados"
            enable_app "$ADDREP_POOL_NAME" "rbd"
        fi
    else
        echo "The specified rbd pool already exists: $ADDREP_POOL_NAME"
    fi
}
del_rbd_rep() {
    echo "--- Del Pool (REP) -------------------------------------------"
    DELREP_NAME=$1
    RULE="rep${3}"
    DELREP_POOL_NAME="$NAME_PREFIX-$DELREP_NAME-$RULE"
    HAS_POOL=$(ceph osd pool ls | grep -c "$DELREP_POOL_NAME")
    if [[ $HAS_POOL -gt 0 ]]; then
        echo "Delete replicated pool $DELREP_POOL_NAME -> $RULE"
        allow_pool_delete
        ceph osd pool rm "$DELREP_POOL_NAME" "$DELREP_POOL_NAME" \
            --yes-i-really-really-mean-it
        deny_pool_delete
    else
        echo "The specified rbd pool does not exist: $DELREP_POOL_NAME"
    fi
}
del_rbd_forced() {
    echo "--- Del Pool (FORCED) ----------------------------------------"
    DELFORCE_NAME=$1
    HAS_POOL=$(ceph osd pool ls | grep -c "$DELFORCE_NAME")
    if [[ $HAS_POOL -gt 0 ]]; then
        echo "Delete pool $DELFORCE_NAME"
        allow_pool_delete
        ceph osd pool rm "$DELFORCE_NAME" "$DELFORCE_NAME" \
            --yes-i-really-really-mean-it
        deny_pool_delete
    else
        echo "The specified pool does not exist: $DELFORCE_NAME"
    fi
}
add_fs_ec() {
    echo "--- Add FS (EC) ----------------------------------------------"
    ADDFSEC_NAME=$1
    RULE="k${3}m${4}"
    POOL_NAME="$NAME_PREFIX-$ADDFSEC_NAME-$NAME_SUFFIX_CFS"
    CFS_DATA="cephfs.$POOL_NAME.data"
    CFS_META="cephfs.$POOL_NAME.meta"
    HAS_FS=$(ceph fs ls | grep -c "$POOL_NAME")
    if [[ $HAS_FS -eq 0 ]]; then
        add_rbd_ec "$1-$NAME_SUFFIX_CFS" "$2" "$3" "$4"
        ceph fs volume create "$POOL_NAME"
        ceph fs add_data_pool "$POOL_NAME" "$POOL_NAME-$RULE"
        wait_for_healthy
        ceph osd pool set "$CFS_DATA" size "$3"
        ceph osd pool set "$CFS_META" size "$3"
        ceph osd pool set "$CFS_DATA" pg_autoscale_mode "$AUTOSACALER_LEVEL"
        ceph osd pool set "$CFS_META" pg_autoscale_mode "$AUTOSACALER_LEVEL"
        ceph osd pool set "$CFS_DATA" bulk "$POOL_BULK"
        ceph osd pool set "$CFS_META" bulk "$POOL_BULK"
        ceph osd pool set "$CFS_DATA" pg_num "$PG_AMOUNT"
        ceph osd pool set "$CFS_META" pg_num "$PG_AMOUNT"
        ceph osd pool set "$POOL_NAME" pg_num "$PG_AMOUNT"
        mount_fs "$ADDFSEC_NAME" 
        echo "Pinning directory '/mnt/$POOL_NAME' to ec pool '$POOL_NAME-$RULE'"
        setfattr -n ceph.dir.layout.pool -v "$POOL_NAME-$RULE" "/mnt/$POOL_NAME"
        unmount_fs "$ADDFSEC_NAME"
        sleep $SLEEPTIME
    else
        echo "The specified filesystem already exists: $POOL_NAME"
    fi
}
del_fs_ec() {
    echo "--- Del FS (EC) ----------------------------------------------"
    DELFSEC_NAME=$1
    RULE="k${3}m${4}"
    POOL_NAME="$NAME_PREFIX-$DELFSEC_NAME-$NAME_SUFFIX_CFS"
    CFS_DATA="cephfs.$POOL_NAME.data"
    CFS_META="cephfs.$POOL_NAME.meta"
    HAS_FS=$(ceph fs ls | grep -c "$POOL_NAME")
    if [[ $HAS_FS -gt 0 ]]; then
        ceph fs set "$POOL_NAME" down true
        wait_for_cfs_stop "$POOL_NAME"
        allow_pool_delete
        ceph fs rm "$POOL_NAME" --yes-i-really-mean-it
        allow_pool_delete
        ceph osd pool rm "$CFS_DATA" "$CFS_DATA" --yes-i-really-really-mean-it
        ceph osd pool rm "$CFS_META" "$CFS_META" --yes-i-really-really-mean-it
        del_rbd_ec "$1-$NAME_SUFFIX_CFS" "$2" "$3" "$4"
        deny_pool_delete
    else
        echo "The specified filesystem does not exist: $POOL_NAME"
    fi
}
add_fs_rep() {
    echo "--- Add FS ---------------------------------------------------"
    ADDFS_NAME=$1
    RULE="rep${2}"
    POOL_NAME="$NAME_PREFIX-$ADDFS_NAME-fs"
    CFS_DATA="cephfs.$POOL_NAME.data"
    CFS_META="cephfs.$POOL_NAME.meta"
    HAS_FS=$(ceph fs ls | grep -c "$POOL_NAME")
    if [[ $HAS_FS -eq 0 ]]; then
        echo "Create filesystem $POOL_NAME -> $RULE"
        sleep "$SLEEPTIME"
        ceph fs volume create "$POOL_NAME"
        ceph osd pool set "$CFS_DATA" pg_autoscale_mode "$AUTOSACALER_LEVEL"
        ceph osd pool set "$CFS_META" pg_autoscale_mode "$AUTOSACALER_LEVEL"
        ceph osd pool set "$CFS_DATA" size "$2"
        ceph osd pool set "$CFS_META" size "$2"
        ceph osd pool set "$CFS_DATA" bulk "$POOL_BULK"
        ceph osd pool set "$CFS_META" bulk "$POOL_BULK"
        ceph osd pool set "$CFS_DATA" pg_num "$PG_AMOUNT"
        ceph osd pool set "$CFS_META" pg_num "$PG_AMOUNT"
        sleep "$SLEEPTIME"
    else
        echo "The specified filesystem already exists: $POOL_NAME"
    fi
}
del_fs_rep() {
    echo "--- Del FS ---------------------------------------------------"
    DELFS_NAME=$1
    RULE="rep${2}"
    POOL_NAME="$NAME_PREFIX-$DELFS_NAME-fs"
    CFS_DATA="cephfs.$POOL_NAME.data"
    CFS_META="cephfs.$POOL_NAME.meta"
    HAS_FS=$(ceph fs ls | grep -c "$POOL_NAME")
    if [[ $HAS_FS -gt 0 ]]; then
        echo "Delete filesystem $POOL_NAME -> $RULE"
        ceph fs set "$POOL_NAME" down true
        wait_for_cfs_stop "$POOL_NAME"
        ceph fs rm "$POOL_NAME" --yes-i-really-mean-it
    else
        echo "The specified filesystem does not exist: $POOL_NAME"
    fi

    HAS_POOLS=$(ceph osd pool ls | grep -c "cephfs.$POOL_NAME" )
    if [[ $HAS_POOLS -gt 0 ]]; then
        echo "Delete related pools"
        wait_for_cfs_stop "$POOL_NAME"
        allow_pool_delete
        ceph osd pool rm "$CFS_DATA" "$CFS_DATA" --yes-i-really-really-mean-it
        ceph osd pool rm "$CFS_META" "$CFS_META" --yes-i-really-really-mean-it
        deny_pool_delete
    fi
}
del_fs_forced() {
    echo "--- Del FS (FORCED) ------------------------------------------"
    DELFSFORCE_NAME=$1
    DELFSFORCE_DATA="cephfs.$DELFSFORCE_NAME.data"
    DELFSFORCE_META="cephfs.$DELFSFORCE_NAME.meta"
    HAS_FS=$(ceph fs ls | grep -c "$DELFSFORCE_NAME")
    if [[ $HAS_FS -gt 0 ]]; then
        ceph fs set "$DELFSFORCE_NAME" down true
        wait_for_cfs_stop "$DELFSFORCE_NAME"
        allow_pool_delete
        ceph fs rm "$DELFSFORCE_NAME" --yes-i-really-mean-it
        allow_pool_delete
        ceph osd pool rm "$DELFSFORCE_DATA" "$DELFSFORCE_DATA" --yes-i-really-really-mean-it
        ceph osd pool rm "$DELFSFORCE_META" "$DELFSFORCE_META" --yes-i-really-really-mean-it
        del_rbd_forced "$DELFSFORCE_NAME"
        deny_pool_delete
    else
        echo "The specified filesystem does not exist: $DELFSFORCE_DATA"
    fi
}
mount_fs() {
    echo "--- Mount FS --------------------------------------------------"
    MNT_NAME=$1
    MNT_POOL_NAME="$NAME_PREFIX-$MNT_NAME-fs"
    HAS_FS=$(ceph fs ls | grep -c "$MNT_POOL_NAME")
    if [[ $HAS_FS -gt 0 ]]; then
        echo "Mount filesystem $MNT_POOL_NAME"
        mkdir -p /mnt/"$MNT_POOL_NAME" 2>/dev/null >/dev/null
        ceph-fuse --client_fs "$MNT_POOL_NAME" \
            -m "$MONITOR_LIST" /mnt/"$MNT_POOL_NAME" 2>/dev/null >/dev/null
        if [[ $? -ne 0 ]] ; then
            echo "Error on mount!"
        else
            echo "Sucessfully mounted"
        fi
    else
        echo "The specified filesystem does not exist: $MNT_POOL_NAME"
    fi
}
unmount_fs() {
    echo "--- Unmount FS ------------------------------------------------"
    UMNT_NAME=$1
    UMNT_POOL_NAME="$NAME_PREFIX-$UMNT_NAME-fs"
    HAS_FS=$(ceph fs ls | grep -c "$UMNT_POOL_NAME")
    if [[ $HAS_FS -gt 0 ]]; then
        echo "Unmount filesystem $UMNT_POOL_NAME"
        fusermount -u /mnt/"$UMNT_POOL_NAME" 2>/dev/null >/dev/null
        rm -rf "/mnt/${UMNT_POOL_NAME:?}" 2>/dev/null >/dev/null
        if [[ $? -ne 0 ]] ; then
            echo "Error on unmount!"
        else
            echo "Sucessfully unmounted"
        fi
    else
        echo "The specified filesystem does not exist: $UMNT_POOL_NAME"
    fi
}

# -----------------------------------------------------------------------------
# Group Targets
# -----------------------------------------------------------------------------

add_all_hosts() {
    echo "--- Add Hosts ------------------------------------------------"
    for i in $(seq 0 $(("${#MEMBERS_CEPH_MANAGE_NAME[*]}" - 1))); do
        item="${MEMBERS_CEPH_MANAGE_NAME[$i]}"
        ip="${MEMBERS_CEPH_MANAGE_IP[$i]}"
        echo "Pinging $item ..."
        ping -c 1 "$item"
        ssh-keyscan "$item" >> ~/.ssh/knwon_hosts
        scp /etc/ceph/ceph.conf "$item":/etc/ceph/
        scp /etc/ceph/ceph.client.admin.keyring "$item":/etc/ceph/
        PUBKEYSTR=$(cat /etc/ceph/ceph.pub)
        ssh "$item" "echo $PUBKEYSTR >> /root/.ssh/authorized_keys"
        sudo ceph orch host add "$item" "$ip"
        if [ "$SLEEPTIME" -gt 0 ] ; then
            echo "Waiting ${SLEEPTIME}s for other hosts..."
            sleep "$SLEEPTIME"
        fi
    done
}
del_all_profiles() {
    echo "--- Delete EC-Profiles ---------------------------------------"
    del_ec_profile "$NAME_PREFIX_PROFILE" "2" "1"
    del_ec_profile "$NAME_PREFIX_PROFILE" "2" "2"
    del_ec_profile "$NAME_PREFIX_PROFILE" "3" "1"
}
add_all_profiles() {
    echo "--- Create EC-Profiles ---------------------------------------"
    add_ec_profile "$NAME_PREFIX_PROFILE" "2" "1" "host"
    add_ec_profile "$NAME_PREFIX_PROFILE" "2" "2" "host"
    add_ec_profile "$NAME_PREFIX_PROFILE" "3" "1" "host"
}
add_all_buckets() {
    echo "--- Add Crush Buckets ----------------------------------------"
    add_bucket "building1" "datacenter" "root=default"
    add_bucket "building2" "datacenter" "root=default"
}
del_all_buckets() {
    echo "--- Add Crush Buckets ----------------------------------------"
    del_bucket "building1"
    del_bucket "building2"
}
enforce_bucket_locations() {
    echo "--- Enforce Bucket Locations ---------------------------------"
    for i in $(seq 0 $(("${#MEMBERS_CEPH_MANAGE_NAME[*]}" - 1))); do
        item="${MEMBERS_CEPH_MANAGE_NAME[$i]}"
        DC="building1"
        if (( i % 2 == 0 )); then
            DC="building2"
        fi
        move_bucket "$item" "root=default datacenter=$DC"
    done
}
enforce_bucket_root() {
    echo "--- Enforce Bucket Locations ---------------------------------"
    for i in $(seq 0 $(("${#MEMBERS_CEPH_MANAGE_NAME[*]}" - 1))); do
        item="${MEMBERS_CEPH_MANAGE_NAME[$i]}"
        move_bucket "$item" "root=default"
    done
}
add_all_rules() {
    echo "--- Del Crush Rules ------------------------------------------"
    add_ec_rule "rule-ec-2dc-k2m1" "citk2m1"
    add_ec_rule "rule-ec-2dc-k2m2" "citk2m2"
    add_ec_rule "rule-ec-2dc-k3m1" "citk3m1"
    add_ec_rule "rule-ec-2dc-k3m2" "citk3m2"
    add_ec_rule "rule-ec-2dc-k4m1" "citk4m1"
    add_ec_rule "rule-ec-2dc-k4m2" "citk4m2"
    add_rep_rule "rule-rep-2dc-hdd" "building1" "host" "hdd"
    add_rep_rule "rule-rep-2dc-ssd" "building2" "host" "ssd"
}
del_all_rules() {
    echo "--- Del Crush Rules ------------------------------------------"
    del_ec_rule "rule-ec-2dc-k2m1"
    del_ec_rule "rule-ec-2dc-k2m2"
    del_ec_rule "rule-ec-2dc-k3m1"
    del_ec_rule "rule-ec-2dc-k3m2"
    del_ec_rule "rule-ec-2dc-k4m1"
    del_ec_rule "rule-ec-2dc-k4m2"
    del_rep_rule "rule-rep-2dc-hdd"
    del_rep_rule "rule-rep-2dc-ssd"
}
add_all_pools() {
    add_rbd_rep  "${TEST_POOL_RBDREP}2" "rep" "2" "true"
    add_rbd_rep  "${TEST_POOL_RBDREP}3" "rep" "3" "true"
    add_rbd_rep  "${TEST_POOL_RBDREP}4" "rep" "4" "true"
    add_rbd_ec  "${TEST_POOL_RBDEC}21" "ec" "2" "1" "true"
    add_rbd_ec  "${TEST_POOL_RBDEC}31" "ec" "3" "1" "true"
    add_rbd_ec  "${TEST_POOL_RBDEC}22" "ec" "2" "2" "true"
}
del_all_pools() {
    del_rbd_rep  "${TEST_POOL_RBDREP}2" "rep" "2" "true"
    del_rbd_rep  "${TEST_POOL_RBDREP}3" "rep" "3" "true"
    del_rbd_rep  "${TEST_POOL_RBDREP}4" "rep" "4" "true"
    del_rbd_ec  "${TEST_POOL_RBDEC}21" "ec" "2" "1" "true"
    del_rbd_ec  "${TEST_POOL_RBDEC}31" "ec" "3" "1" "true"
    del_rbd_ec  "${TEST_POOL_RBDEC}22" "ec" "2" "2" "true"
}
add_all_fs() {
    add_fs_rep "${TEST_POOL_CFSREP}2" 2
    add_fs_rep "${TEST_POOL_CFSREP}3" 3
    add_fs_rep "${TEST_POOL_CFSREP}4" 4
    add_fs_ec "${TEST_POOL_CFSEC}21" "cfsec" "2" "1"
    add_fs_ec "${TEST_POOL_CFSEC}22" "cfsec" "2" "2"
    add_fs_ec "${TEST_POOL_CFSEC}31" "cfsec" "3" "1"
}
del_all_fs() {
    del_fs_rep "${TEST_POOL_CFSREP}2" 2
    del_fs_rep "${TEST_POOL_CFSREP}3" 3
    del_fs_rep "${TEST_POOL_CFSREP}4" 4
    del_fs_ec "${TEST_POOL_CFSEC}21" "cfsec" "2" "1"
    del_fs_ec "${TEST_POOL_CFSEC}22" "cfsec" "2" "2"
    del_fs_ec "${TEST_POOL_CFSEC}31" "cfsec" "3" "1"
}
mount_all_fs() {
    mount_fs "${TEST_POOL_CFSREP}2"
    mount_fs "${TEST_POOL_CFSREP}3"
    mount_fs "${TEST_POOL_CFSREP}4"
    mount_fs "${TEST_POOL_CFSEC}21"
    mount_fs "${TEST_POOL_CFSEC}22"
    mount_fs "${TEST_POOL_CFSEC}31"
}
unmount_all_fs() {
    unmount_fs "${TEST_POOL_CFSREP}2"
    unmount_fs "${TEST_POOL_CFSREP}3"
    unmount_fs "${TEST_POOL_CFSREP}4"
    unmount_fs "${TEST_POOL_CFSEC}21"
    unmount_fs "${TEST_POOL_CFSEC}22"
    unmount_fs "${TEST_POOL_CFSEC}31"
}
add_all_disks() {
    for i in $(seq 0 $(("${#MEMBERS_CEPH_MANAGE_NAME[*]}" - 1))); do
        item="${MEMBERS_CEPH_MANAGE_NAME[$i]}"
        for j in $(seq 0 $(("${#PARSED_ENTITIES[*]}" - 1))); do
            device="${PARSED_ENTITIES[$j]}"
            sudo ceph orch daemon add osd "$item:$device"
            if [ "$SLEEPTIME" -gt 0 ] ; then
                echo "Waiting ${SLEEPTIME}s for other hosts..."
                sleep "$SLEEPTIME"
            fi
        done
        if [ "$SLEEPTIME" -gt 0 ] ; then
            echo "Waiting ${SLEEPTIME}s for other hosts..."
            sleep "$SLEEPTIME"
        fi
    done
}
status_cluster() {
    echo ""
    echo "--- Status Cluster --------------------------------------------"
    ceph -s
    echo ""
    echo "--- Status Pools ----------------------------------------------"
    HEALTH=$(ceph health)
    EC_POOLS=$(ceph osd pool ls | grep -e "-k[0-9]m[0-9]" | tr "\n" " ")
    REP_POOLS=$(ceph osd pool ls | grep -e "-rep[0-9]" -e "-[a-zA-Z]*[0-9]\{1\}-fs" | tr "\n" " ")
    RBD_POOLS=$(rados lspools | tr "\n" " ")
    CFS_POOLS=$(ceph osd pool ls | grep -e "cephfs.$NAME_PREFIX" | tr "\n" " ")
    PG_STATS=$(ceph pg stat)
    FS_LS=$(ceph fs ls | grep "name: $NAME_PREFIX-" \
        | cut -d " " -f 2 | tr -d "\n" | tr "," " ")
    echo "     Health: $HEALTH" 
    echo "PG    Stats: $PG_STATS"
    echo "RADOS Pools: $RBD_POOLS"
    echo "REP   Pools: $REP_POOLS"
    echo "EC    Pools: $EC_POOLS"
    echo ""
    echo "--- Status Filesystem -----------------------------------------"
    echo "Filesystems: $FS_LS"
    # shellcheck disable=SC2206
    arr=($FS_LS)
    echo "FS    Pools: $CFS_POOLS"
    echo "FS   Status:"
    for i in "${arr[@]}"
    do
        STATUS=$(ceph fs status "$i" \
            | grep -e "active" -e "stopping" | column -t | cut -d " " -f 3 )
        printf "%s \t-> %s\n" "$i" "$STATUS"
    done
}
# -----------------------------------------------------------------------------
# Group Targets
# -----------------------------------------------------------------------------
status_storage() {
    echo "--- Status Storage --------------------------------------------"
    echo ""
    echo "Ceph: "
    ceph df
    echo ""
    echo "Rados: "
    rados df
}
status_crush() {
    echo "--- Status Crush ----------------------------------------------"
    echo ""
    echo "Rules: "
    ceph osd crush rule ls
    echo ""
    echo "Buckets: "
    ceph osd crush dump | jq ".buckets[].name"
    echo ""
    echo "Tree: "
    ceph osd crush tree --show-shadow
}
allow_pool_delete() {
    echo "Allowing pool delete"
    ceph tell mon.* injectargs --mon_allow_pool_delete true >/dev/null 2>&1
}
deny_pool_delete() {
    echo "Denying pool delete"
    ceph tell mon.* injectargs --mon_allow_pool_delete false >/dev/null 2>&1
}
wait_for_healthy() {
    IS_HEALTHY=$(ceph -s | grep -c "HEALTH_OK")
    if [[ $IS_HEALTHY -eq 1 ]]; then
        echo "Cluster is healthy! Loop omitted..."
        return 0
    fi
    echo "Cluster is unhealthy! Waiting can take a couple of seconds..."
    while [[ $(ceph -s | grep -c "HEALTH_OK") -eq 0 ]]
    do
        sleep 1
    done
    echo "Filesystem healthy! Resuming operations now..."
}
wait_for_cfs_stop() {
    sleep 1
    FS_NAME=$1
    IS_STOPPING=$(ceph fs status "$FS_NAME" | grep -c "stopping")
    if [[ $IS_STOPPING -eq 0 ]]; then
        echo "Pool is not stopping! Loop omitted..."
        return 0
    fi
    echo "Filesystem is currently stopping! Waiting can take around 30s..."
    while [[ $(ceph fs status "$FS_NAME" | grep -c "stopping") -eq 1 ]]
    do
        sleep 1
    done
    echo "Filesystem stopped! Resuming operations now..."
}
while getopts ":d:a:n:N:R:r:k:m:p:s:b:o:t:l:h " o; do
    # echo "Param: '$o' -> '$OPTARG'"
    case "$o" in
        a)
            ACTION=${OPTARG}
            ;;
        d)
            DISK_PREFIX=${OPTARG}
            ;;
        n)
            ENTITY_NAME=${OPTARG}
            ;;
        N)
            ENTITY_LIST=${OPTARG}
            ;;
        R)
            ENTITY_RELATED=${OPTARG}
            ;;
        r)
            REP_SIZE=${OPTARG}
            ;;
        k)
            K_SIZE=${OPTARG}
            ;;
        m)
            M_SIZE=${OPTARG}
            ;;
        p)
            PG_AMOUNT=${OPTARG}
            ;;
        s)
            AUTOSACALER_LEVEL=${OPTARG}
            ;;
        b)
            POOL_BULK=${OPTARG}
            ;;
        o)
            POOL_EC_OVERWRITES=${OPTARG}
            ;;
        t)
            BUCKET_TYPE=${OPTARG}
            ;;
        l)
            BUCKET_LOCATION=${OPTARG}
            ;;
        h)
            usage
            exit 0
            ;;
        *)
            echo ""
            echo "Unknown argument: $o"
            usage
            exit 1
            ;;
    esac
done
shift $((OPTIND-1))

read_entitylist
read_nodes_from_config
case "$ACTION" in
    "status-cluster")
        status_cluster
        ;;
    "status-storage")
        status_storage
        ;;
    "status-crush")
        status_crush
        ;;
    "init-cluster")
        init_cluster
        ;;
    "create-dashboard")
        create_dashboard
        ;;
    "add-all-hosts")
        add_all_hosts
        ;;
    "add-all-disks")
        add_all_disks
        ;;
    "bootstrap-cluster")
        init_cluster
        create_dashboard
        add_all_hosts
        add_all_disks
        enforce_bucket_root
        del_all_profiles
        del_all_buckets
        del_all_rules
        add_all_profiles
        add_all_buckets
        add_all_rules
        enforce_bucket_locations
        ;;
    "add-all-buckets")
        add_all_buckets
        ;;
    "del-all-buckets")
        del_all_buckets
        ;;
    "add-all-rules")
        add_all_rules
        ;;
    "del-all-rules")
        del_all_rules
        ;;
    "add-all-profiles")
        add_all_profiles
        ;;
    "del-all-profiles")
        del_all_profiles
        ;;
    "enforce-bucket-root")
        enforce_bucket_root
        ;;
    "enforce-bucket-locations")
        enforce_bucket_locations
        ;;
    "add-all-crush")
        add_all_profiles
        add_all_buckets
        add_all_rules
        ;;
    "del-all-crush")
        enforce_bucket_root
        del_all_profiles
        del_all_buckets
        del_all_rules
        ;;
    "recreate-all-crush")
        enforce_bucket_root
        del_all_profiles
        del_all_buckets
        del_all_rules
        add_all_profiles
        add_all_buckets
        add_all_rules
        enforce_bucket_locations
        ;;
    "add-all-fs")
        add_all_fs
        ;;
    "del-all-fs")
        del_all_fs
        ;;
    "mount-all-fs")
        mount_all_fs
        ;;
    "unmount-all-fs")
        unmount_all_fs
        ;;
    "add-all-pools")
        add_all_pools
        ;;
    "del-all-pools")
        del_all_pools
        ;;
    "recreate-all-pools")
        del_all_fs
        del_all_pools
        del_all_profiles
        add_all_profiles
        del_all_buckets
        add_all_buckets
        del_all_rules
        add_all_rules
        add_all_pools
        add_all_fs
        ;;
    "create-all")
        init_cluster
        create_dashboard
        add_all_hosts
        add_all_disks
        del_all_fs
        del_all_pools
        add_all_profiles
        add_all_buckets
        add_all_rules
        enforce_bucket_locations
        add_all_pools
        add_all_fs
        ;;
    "add-bucket")
        [[ -z "$BUCKET_TYPE" ]] && echo "Type is missing" && usage && exit 1
        [[ -z "$ENTITY_NAME" ]] && echo "Name is missing" && usage && exit 1
        add_bucket "$ENTITY_NAME" "$BUCKET_TYPE" "$BUCKET_LOCATION"
        ;;
    "del-bucket")
        [[ -z "$ENTITY_NAME" ]] && echo "Name is missing" && usage && exit 1
        del_bucket "$ENTITY_NAME"
        ;;
    "move-bucket")
        [[ -z "$ENTITY_NAME" ]] && echo "Name is missing" && usage && exit 1
        [[ -z "$BUCKET_LOCATION" ]] && echo "Bucket location is missing" && usage && exit 1
        move_bucket "$ENTITY_NAME" "$BUCKET_LOCATION"
        ;;
    "add-ec-rule")
        [[ -z "$ENTITY_NAME" ]] && echo "Name is missing" && usage && exit 1
        [[ -z "$ENTITY_RELATED" ]] && echo "Related name is missing" && usage && exit 1
        add_ec_rule "$ENTITY_NAME" "$ENTITY_RELATED"
        ;;
    "del-ec-rule")
        [[ -z "$ENTITY_NAME" ]] && echo "Name is missing" && usage && exit 1
        del_ec_rule "$ENTITY_NAME"
        ;;
    "add-rep-rule")
        [[ -z "$BUCKET_CLASS" ]] && echo "Bucket class is missing" && usage && exit 1
        [[ -z "$BUCKET_TYPE" ]] && echo "Bucket Type is missing" && usage && exit 1
        [[ -z "$ENTITY_NAME" ]] && echo "Name is missing" && usage && exit 1
        [[ -z "$ENTITY_RELATED" ]] && echo "Related name is missing" && usage && exit 1
        add_rep_rule "$ENTITY_NAME" "$ENTITY_RELATED" "$BUCKET_TYPE" "$ENTITY_CLASS"
        ;;
    "del-rep-rule")
        [[ -z "$ENTITY_NAME" ]] && echo "Name is missing" && usage && exit 1
        del_rep_rule "$ENTITY_NAME"
        ;;
    "add-ec-profile")
        [[ -z "$K_SIZE" ]] && echo "EC size (K) is missing" && usage && exit 1
        [[ -z "$M_SIZE" ]] && echo "EC size (M) is missing" && usage && exit 1
        [[ -z "$BUCKET_TYPE" ]] && echo "Bucket type is missing" && usage && exit 1
        [[ -z "$ENTITY_NAME" ]] && echo "Name is missing" && usage && exit 1
        add_ec_profile "$ENTITY_NAME" "$K_SIZE" "$M_SIZE" "$BUCKET_TYPE"
        ;;
    "del-ec-profile")
        [[ -z "$K_SIZE" ]] && echo "EC size (K) is missing" && usage && exit 1
        [[ -z "$M_SIZE" ]] && echo "EC size (M) is missing" && usage && exit 1
        [[ -z "$ENTITY_NAME" ]] && echo "Name is missing" && usage && exit 1
        del_ec_profile "$ENTITY_NAME" "$K_SIZE" "$M_SIZE"
        ;;
    "add-rbd-ec")
        [[ -z "$K_SIZE" ]] && echo "EC size (K) is missing" && usage && exit 1
        [[ -z "$M_SIZE" ]] && echo "EC size (M) is missing" && usage && exit 1
        [[ -z "$ENTITY_NAME" ]] && echo "Name is missing" && usage && exit 1
        add_rbd_ec  "${ENTITY_NAME}$K_SIZE$M_SIZE" "rbdec" "$K_SIZE" "$M_SIZE" "true"
        ;;
    "del-rbd-ec")
        [[ -z "$K_SIZE" ]] && echo "EC size (K) is missing" && usage && exit 1
        [[ -z "$M_SIZE" ]] && echo "EC size (M) is missing" && usage && exit 1
        [[ -z "$ENTITY_NAME" ]] && echo "Name is missing" && usage && exit 1
        del_rbd_ec  "${ENTITY_NAME}$K_SIZE$M_SIZE" "rbdec" "$K_SIZE" "$M_SIZE" "true"
        ;;
    "add-rbd-rep")
        [[ -z "$REP_SIZE" ]] && echo "Replica size is missing" && usage && exit 1
        [[ -z "$ENTITY_NAME" ]] && echo "Name is missing" && usage && exit 1
        add_rbd_rep  "${ENTITY_NAME}$REP_SIZE" "rbdrep" "$REP_SIZE" "true"
        ;;
    "del-rbd-rep")
        [[ -z "$REP_SIZE" ]] && echo "Replica size is missing" && usage && exit 1
        [[ -z "$ENTITY_NAME" ]] && echo "Name is missing" && usage && exit 1
        del_rbd_rep  "${ENTITY_NAME}$REP_SIZE" "rbdrep" "$REP_SIZE" "true"
        ;;
    "del-rbd-forced")
        [[ -z "$ENTITY_NAME" ]] && echo "Name is missing" && usage && exit 1
        del_rbd_forced "${ENTITY_NAME}"
        ;;
    "add-fs-rep")
        [[ -z "$REP_SIZE" ]] && echo "Replica size is missing" && usage && exit 1
        [[ -z "$ENTITY_NAME" ]] && echo "Name is missing" && usage && exit 1
        add_fs_rep "${ENTITY_NAME}$REP_SIZE" "$REP_SIZE"
        ;;
    "del-fs-rep")
        [[ -z "$REP_SIZE" ]] && echo "Replica size is missing" && usage && exit 1
        [[ -z "$ENTITY_NAME" ]] && echo "Name is missing" && usage && exit 1
        del_fs_rep "${ENTITY_NAME}$REP_SIZE" "$REP_SIZE"
        ;;
    "add-fs-ec")
        [[ -z "$K_SIZE" ]] && echo "EC size (K) is missing" && usage && exit 1
        [[ -z "$M_SIZE" ]] && echo "EC size (M) is missing" && usage && exit 1
        [[ -z "$ENTITY_NAME" ]] && echo "Name is missing" && usage && exit 1
        add_fs_ec "${ENTITY_NAME}$K_SIZE$M_SIZE" "cfsec" "$K_SIZE" "$M_SIZE"
        ;;
    "del-fs-ec")
        [[ -z "$K_SIZE" ]] && echo "EC size (K) is missing" && usage && exit 1
        [[ -z "$M_SIZE" ]] && echo "EC size (M) is missing" && usage && exit 1
        [[ -z "$ENTITY_NAME" ]] && echo "Name is missing" && usage && exit 1
        del_fs_ec "${ENTITY_NAME}$K_SIZE$M_SIZE" "cfsec" "$K_SIZE" "$M_SIZE"
        ;;
    "del-fs-forced")
        [[ -z "$ENTITY_NAME" ]] && echo "Name is missing" && usage && exit 1
        del_fs_forced "${ENTITY_NAME}"
        ;;
    "mount-fs")
        [[ -z "$ENTITY_NAME" ]] && echo "Name is missing" && usage && exit 1
        SIZE_EXT=""
        if [[ "$K_SIZE" != ""  && "$M_SIZE" != "" ]]; then
            SIZE_EXT="$K_SIZE$M_SIZE"
        elif [[ "$REP_SIZE" != "" ]]; then
            SIZE_EXT="$REP_SIZE"
        else
            echo "No pool sizes given! Trying without a size..."
        fi
        mount_fs "${ENTITY_NAME}$SIZE_EXT"
        ;;
    "unmount-fs")
        [[ -z "$ENTITY_NAME" ]] && echo "Name is missing" && usage && exit 1
        SIZE_EXT=""
        if [[ "$K_SIZE" != ""  && "$M_SIZE" != "" ]]; then
            SIZE_EXT="$K_SIZE$M_SIZE"
        elif [[ "$REP_SIZE" != "" ]]; then
            SIZE_EXT="$REP_SIZE"
        else
            echo "No pool sizes given! Trying without a size..."
        fi
        unmount_fs "${ENTITY_NAME}$SIZE_EXT"
        ;;
    *)
        echo ""
        echo "Unknown action: $ACTION"
        usage
        exit 1
        ;;
esac
echo "-------------------------------------------------------------"
echo ""
