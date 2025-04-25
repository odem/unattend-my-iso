#!/bin/bash
# shellcheck disable=SC1090,2005,2029,2048

# Environment variables
POSTINST_PATH=/opt/umi/postinstall
cd "$POSTINST_PATH" || exit 1
envfile=../config/env.bash
if [[ -f "$envfile" ]]; then
    # shellcheck disable=SC1090
    source "$envfile"
fi

LEADER_NAME=$DEFAULT_LEADER_PROXMOX
MEMBERS_PROX_MANAGE_NAME=()
VERBOSE=0
FORCE=0
CLEANUP_STORAGE=0
CEPH_VERSION=squid
SLEEP_SHORT=1
SLEEP_LONG=10
SCRIPTNAME=/opt/umi/postinstall/manage/manage_ceph_cluster_hyper.bash
SSHOPTS="-o StrictHostKeyChecking=no"
ENTITY_NAME=
ENTITY_SIZE=
PG_NUM_DEFAULT=16
PG_AUTOSCALE=warn
ENTITY_LIST=""
usage() {
    echo "      "
    echo "Usage: $0 ACTION [ FLAG1 FLAG2 ... ] [ PARAM1 PARAM2 ... ]"
    echo "      "
    echo "    Actions:"
    echo "      -a ceph-install       : Installs required ceph packages"
    echo "      -a bootstrap-cluster  : Creates cluster and adds all nodes"
    echo "      -a wipe-cluster       : Removes all nodes and deletes cluster"
    echo "      -a add-cluster        : Initialize new cluster"
    echo "      -a del-cluster        : Removes cluster (Must only contain leader node)"
    echo "      -a add-node           : Joins this node into cluster"
    echo "      -a del-node           : Removes this node from cluster"
    echo "      -a add-rbd            : Creates new rbd pool"
    echo "      -a del-rbd            : Removes rbd pool from cluster"
    echo "      -a add-fs             : Creates new filesystem"
    echo "      -a del-fs             : Removes fileystem from cluster"
    echo "      -a add-osd            : Adds new osd to cluster"
    echo "      -a del-osd            : Removes osd from cluster"
    echo "      -a add-all-osd        : Adds specified osd on each node in cluster"
    echo "      -a del-all-osd        : Removes specified osd on each node in cluster"
    echo "      -a status-cluster     : Print ceph status"
    echo "      -a status-pools       : Print pool status"
    echo "      -a status-disks       : Print disk status"
    echo "      "
    echo "    Flags:"
    echo "      -C                    : Wipes disk"
    echo "      -S                    : Include proxmox storages"
    echo "      -f                    : Force action if needed"
    echo "      -v                    : Verbose output (first flag)"
    echo "      -h                    : Print usage"
    echo "      "
    echo "    Parameters:"
    echo "      -s size               : Size of the entity"
    echo "      -p pg_num             : Initial pg size"
    echo "      -P pg_autoscale_mode  : on, off or warn (Default: warn)"
    echo "      -n Entity_Name        : Name of the entity to operate on"
    echo "      -N Entity list        : Entity list"
    echo "      -L Leader_Name        : No IP! MUST be a hostname!"
    echo "      "
}
while getopts "a:n:L:p:P:N:s:S :h v f C " o; do
    [[ $VERBOSE -eq 1 ]] && echo "Processing option: -$o with value: ${OPTARG}"
    case "$o" in
        a)
            ACTION=${OPTARG}
            ;;
        n)
            ENTITY_NAME=${OPTARG}
            ;;
        N)
            ENTITY_LIST=${OPTARG}
            ;;
        s)
            ENTITY_SIZE=${OPTARG}
            ;;
        p)
            PG_NUM_DEFAULT=${OPTARG}
            ;;
        P)
            PG_AUTOSCALE=${OPTARG}
            ;;
        L)
            LEADER_NAME=${OPTARG}
            ;;
        C)
            CLEANUP_STORAGE=1
            ;;
        S)
            ADD_STORAGE=1
            ;;
        v)
            VERBOSE=1
            ;;
        f)
            FORCE=1
            ;;
        h)
            usage
            exit 0
            ;;
        *)
            echo "Not a valid argument: '$1'"
            usage
            exit 1
            ;;
    esac
done
shift $((OPTIND-1))

wait_for_ceph() {
    SLEEPTEXT=$1
    SLEEPTIME=$2
    # shellcheck disable=SC2059
    printf "$SLEEPTEXT" "$SLEEPTIME"
    sleep "$SLEEPTIME" 
}
compare_host2leader() {
    if [[ "$MANAGE_HOST" != "$LEADER_NAME" ]] ; then
        return 1
    else
        return 0
    fi
}
read_osdlist() {
    if [[ "$ENTITY_LIST" != "" ]]; then
        IFS=',' read -ra PARSED_ENTITIES <<< "$ENTITY_LIST"
        LINE="${#PARSED_ENTITIES[*]} parsed entities: ${PARSED_ENTITIES[*]}"
        [[ $VERBOSE -eq 1 ]] && echo "$LINE"
    fi
}
read_nodes_from_config() {
    if [[ "$NODES_PROX_MANAGE_NAME" != "" ]]; then
        IFS=',' read -ra MEMBERS_PROX_MANAGE_NAME <<< "$NODES_PROX_MANAGE_NAME"
        LINE="${#MEMBERS_PROX_MANAGE_NAME[*]} configured cluster Members: ${MEMBERS_PROX_MANAGE_NAME[*]}"
        [[ $VERBOSE -eq 1 ]] && echo "$LINE"
    fi
}
add_node_components() {
    echo "-> Create components (mon): "
    pveceph mon create
    wait_for_ceph "Waiting %ss for ceph initialization (mon)\n" "$SLEEP_SHORT"
    echo "-> Create components (mgr): "
    pveceph mgr create
    wait_for_ceph "Waiting %ss for ceph initialization (mgr)\n" "$SLEEP_SHORT"
    echo "-> Create components (mds): "
    pveceph mds create
    wait_for_ceph "Waiting %ss for ceph initialization (mds)\n" "$SLEEP_SHORT"
}
del_node_components() {
    echo "-> Destroy components (mon): "
    pveceph mon destroy "$MANAGE_HOST"
    echo "-> Destroy components (mgr): "
    pveceph mgr destroy "$MANAGE_HOST"
    echo "-> Destroy components (mgr): "
    pveceph mds destroy "$MANAGE_HOST"
}
purge_local_config() {
    echo "-> Kill daemons: "
    killall -9 ceph-mon ceph-mgr ceph-mds >/dev/null 2>&1
    echo "-> Purging via pveceph: "
    pveceph purge
    echo "-> Purging local ceph config: "
    rm -rf rm -rf /etc/ceph/ceph.conf
    rm -rf rm -rf /etc/pve/ceph.conf
}
ceph_install() {
    echo "--- Ceph Install --------------------------------------------"
    echo "=> Trying to install required packages on $MANAGE_HOST"
    CEPH=$(which pveceph)
    if [[ "$CEPH" != "" ]]; then
        echo "-> Installing ceph ($CEPH_VERSION): "
        echo "yJ" | pveceph install -repository no-subscription -version "$CEPH_VERSION"
    else
        echo "Error! The pveceph tool was not found. Path found: $CEPH"
    fi
}
add_cluster() {
    echo "--- Create Cluster ------------------------------------------"
    echo "=> Trying to create cluster via $MANAGE_HOST"
    compare_host2leader
    HOST_CHECK=$?
    if [[ $HOST_CHECK -eq 0 ]] ; then
        echo "-> Initialize network ($STORAGE_NET.0/24): "
        pveceph init --network "${STORAGE_NET}.0/24"
        wait_for_ceph "Waiting %ss for ceph initialization (network)\n" "$SLEEP_LONG"
        add_node_components
    else
        echo "Action must be executed on leader host! '$MANAGE_HOST' vs '$LEADER_NAME'"
    fi
    [[ $VERBOSE -eq 1 ]] && status_cluster
}
del_cluster() {
    echo "--- Remove Cluster ------------------------------------------"
    echo "=> Trying to remove current cluster via $MANAGE_HOST"
    echo "-> Delete cluster info: "
    compare_host2leader
    HOST_CHECK=$?
    if [[ $HOST_CHECK -eq 0 ]] ; then
        del_node_components
        purge_local_config
    else
        echo "Action must be executed on leader host! '$MANAGE_HOST' vs '$LEADER_NAME'"
    fi
}
add_node() {
    echo "--- Add Node ------------------------------------------------"
    echo "=> Trying to add node via $MANAGE_HOST"
    [[ $VERBOSE -eq 1 ]] && status_cluster
    compare_host2leader
    HOST_CHECK=$?
    if [[ $HOST_CHECK -eq 1 ]] ; then
        add_node_components
    else
        echo "Action must NOT be executed on leader host! '$MANAGE_HOST' vs '$LEADER_NAME'"
    fi
}
del_node() {
    echo "--- Delete Node ---------------------------------------------"
    echo "=> Trying to delete node via $MANAGE_HOST"
    [[ $VERBOSE -eq 1 ]] && status_cluster
    compare_host2leader
    HOST_CHECK=$?
    if [[ $HOST_CHECK -eq 1 ]] ; then
        del_node_components
        purge_local_config
    else
        echo "Action must NOT be executed on leader host! '$MANAGE_HOST' vs '$LEADER_NAME'"
    fi
}

get_osd_id() {
    DEVICENAME=$1
    FOUND=$(ceph-volume lvm list "$DEVICENAME" | grep -c "osd id")
    if [[ "$FOUND" -gt 0 ]] ; then
        ID=$(ceph-volume lvm list "$DEVICENAME" | grep "osd id" | awk '{print $3}')
        echo "$ID"
        return 0
    fi
    echo -1
    return 1
}
clean_osd() {
    device=$1
    OSD_ID=$(get_osd_id "$device")
    if [[ "$CLEANUP_STORAGE" -eq 1  ]]; then
        vgroup=$(pvs --no-headings | grep "$device" | awk '{print $2}')
        if [[ "$OSD_ID" != "-1" ]]; then
            echo "Device is still in use by ceph: $OSD_ID"
        fi
        if [[ "$vgroup" != "" ]]; then
            echo "Device is still in use by lvm: $device"
            # ceph-volume lvm zap "$ENTITY_NAME"
            vgremove -y "$vgroup"
            wipefs -a "$device"
        fi
    fi
}
add_osd() {
    echo "--- Add OSD -------------------------------------------------"
    echo "=> Trying to add osd via $MANAGE_HOST"
    if [[ ${#PARSED_ENTITIES[*]} -gt 0 ]] ; then
        echo "-> Add OSD list (${ENTITY_LIST[*]}): "
        for device in ${PARSED_ENTITIES[*]}; do
            OSD_ID=$(get_osd_id "$device")
            clean_osd "$device"
            if [[ "$OSD_ID" == "-1" ]]; then
                echo "-> Create OSD ($device): "
                pveceph osd create "$device"
            else
                echo "OSD is already in use"
            fi
        done;
    else
        echo "-> Cleanup OSD ($ENTITY_NAME): "
        clean_osd "$ENTITY_NAME"
        OSD_ID=$(get_osd_id "$device")
        if [[ "$OSD_ID" == "-1" ]]; then
            echo "-> Create OSD ($ENTITY_NAME): "
            pveceph osd create "$ENTITY_NAME"
        else
            echo "OSD is already in use"
        fi
    fi
    [[ $VERBOSE -eq 1 ]] && status_disks
}
del_osd() {
    echo "--- Delete OSD ----------------------------------------------"
    echo "=> Trying to delete osd via $MANAGE_HOST"
    if [[ ${#PARSED_ENTITIES[*]} -gt 0 ]] ; then
        echo "-> Delete OSD list (${ENTITY_LIST[*]}): "
        for device in ${PARSED_ENTITIES[*]}; do
            OSD_ID=$(get_osd_id "$device")
            if [[ "$OSD_ID" -ge 0 ]]; then
                echo "-> Stop OSD: osd id '$OSD_ID'"
                ceph osd down osd."${OSD_ID}"
                ceph osd out osd."${OSD_ID}"
                ceph osd stop osd."${OSD_ID}"
                umount "${device}"
                echo "-> Delete OSD: "
                pveceph osd destroy "$OSD_ID" --cleanup "$CLEANUP_STORAGE"
            fi
        done;
    else
        OSD_ID=$(get_osd_id "$ENTITY_NAME")
        if [[ "$OSD_ID" -ge 0 ]]; then
            echo "-> Stop OSD: osd id '$OSD_ID'"
            ceph osd down osd."${OSD_ID}"
            ceph osd out osd."${OSD_ID}"
            ceph osd stop osd."${OSD_ID}"
            umount "${device}"
            echo "-> Delete OSD: "
            pveceph osd destroy "$OSD_ID" --cleanup "$CLEANUP_STORAGE"
        fi
    fi
    [[ $VERBOSE -eq 1 ]] && status_disks
}

add_rbd() {
    echo "--- Add RBD Pool --------------------------------------------"
    echo "=> Trying to add pool via $MANAGE_HOST"
    compare_host2leader
    HOST_CHECK=$?
    if [[ $HOST_CHECK -eq 0 ]] ; then
        echo "-> Create RBD Pool ($ENTITY_NAME): "
        pveceph pool create "$ENTITY_NAME" \
            -pg_num "$PG_NUM_DEFAULT" \
            -pg_num_min "$PG_NUM_DEFAULT" \
            --pg_autoscale_mode "$PG_AUTOSCALE" \
            --application rbd \
            --add_storages "$ADD_STORAGE" \
            --size "$ENTITY_SIZE" \
            --min_size "$ENTITY_SIZE"
    else
        echo "Action must be executed on leader host! '$MANAGE_HOST' vs '$LEADER_NAME'"
    fi
}
del_rbd() {
    echo "--- Del RBD Pool --------------------------------------------"
    echo "=> Trying to remove pool via $MANAGE_HOST"
    compare_host2leader
    HOST_CHECK=$?
    if [[ $HOST_CHECK -eq 0 ]] ; then
        echo "-> Delete RBD Pool ($ENTITY_NAME): "
        pveceph pool destroy "$ENTITY_NAME" --remove_storages 1 --force "$FORCE"
    else
        echo "Action must be executed on leader host! '$MANAGE_HOST' vs '$LEADER_NAME'"
    fi
}

add_fs() {
    echo "--- Add FS Pool ---------------------------------------------"
    echo "=> Trying to add fs via $MANAGE_HOST"
    compare_host2leader
    HOST_CHECK=$?
    if [[ $HOST_CHECK -eq 0 ]] ; then
        echo "-> Create FS Pool ($ENTITY_NAME): "
        pveceph fs create -name "$ENTITY_NAME" \
            -add-storage "$ADD_STORAGE" \
            -pg_num "$PG_NUM_DEFAULT"
        echo "-> Set size data pool ($ENTITY_SIZE): "
        pveceph pool set "${ENTITY_NAME}_data" \
            --pg_num "$PG_NUM_DEFAULT" \
            --pg_num_min "$PG_NUM_DEFAULT" \
            --pg_autoscale_mode "$PG_AUTOSCALE" \
            --application cephfs \
            --size "$ENTITY_SIZE" \
            --min_size "$ENTITY_SIZE"
        echo "-> Set size metadata pool ($ENTITY_SIZE): "
        pveceph pool set "${ENTITY_NAME}_metadata" \
            --pg_num "$PG_NUM_DEFAULT" \
            --pg_num_min "$PG_NUM_DEFAULT" \
            --pg_autoscale_mode "$PG_AUTOSCALE" \
            --application cephfs \
            --size "$ENTITY_SIZE" \
            --min_size "$ENTITY_SIZE"
    else
        echo "Action must be executed on leader host! '$MANAGE_HOST' vs '$LEADER_NAME'"
    fi
}
del_fs() {
    echo "--- Del FS Pool ---------------------------------------------"
    echo "=> Trying to remove fs via $MANAGE_HOST"
    compare_host2leader
    HOST_CHECK=$?
    if [[ $HOST_CHECK -eq 0 ]] ; then
        echo "-> Down the filesystem ($ENTITY_NAME): "
        ceph fs fail "$ENTITY_NAME"
        echo "-> Delete FS Pool ($ENTITY_NAME): "
        pveceph fs destroy "$ENTITY_NAME"
        pveceph pool destroy "${ENTITY_NAME}_data"
        pveceph pool destroy "${ENTITY_NAME}_metadata"
    else
        echo "Action must be executed on leader host! '$MANAGE_HOST' vs '$LEADER_NAME'"
    fi
}
add_all_osd() {
    echo "--- Add All OSD ---------------------------------------------"
    echo "=> Trying to add all osd via $MANAGE_HOST"
    echo ""
    for node in ${MEMBERS_PROX_MANAGE_NAME[*]}; do
        echo "### SSH: Calling to $node (add-osd) ###"
        ssh "$SSHOPTS" "root@$node" "$SCRIPTNAME -a add-osd -C -N $ENTITY_LIST"
    done;
}
del_all_osd() {
    echo "--- Del All OSD ---------------------------------------------"
    echo "=> Trying to delete all osd via $MANAGE_HOST"
    echo ""
    for node in ${MEMBERS_PROX_MANAGE_NAME[*]}; do
        echo "### SSH: Calling to $node (del-osd) ###"
        ssh "$SSHOPTS" "root@$node" "$SCRIPTNAME -a del-osd -C -N $ENTITY_LIST"
    done;
}

bootstrap_cluster() {
    echo "--- Bootstrap Cluster ---------------------------------------"
    echo "=> Trying to bootstrap via $MANAGE_HOST"
    echo ""
    compare_host2leader
    HOST_CHECK=$?
    if [[ $HOST_CHECK -eq 0 ]] ; then
        add_cluster
        for node in ${MEMBERS_PROX_MANAGE_NAME[*]}; do
            if [[ "$node" != "$LEADER_NAME" ]] ; then
                echo "### SSH: Calling to $node (add-node) ###"
                ssh "$SSHOPTS" "root@$node" "$SCRIPTNAME -a add-node"
            fi
            echo "### SSH: Calling to $node (add-osd) ###"
            ssh "$SSHOPTS" "root@$node" "$SCRIPTNAME -a add-osd -N $ENTITY_LIST"
        done;
    else
        echo "Action must be executed on leader host! '$MANAGE_HOST' vs '$LEADER_NAME'"
    fi
    [[ $VERBOSE -eq 1 ]] && status_cluster
}
wipe_cluster() {
    echo "--- Wipe Cluster --------------------------------------------"
    echo "=> Trying to wipe cluster via $MANAGE_HOST"
    [[ $VERBOSE -eq 1 ]] && status_cluster
    echo ""
    compare_host2leader
    HOST_CHECK=$?
    if [[ $HOST_CHECK -eq 0 ]] ; then
        for node in ${MEMBERS_PROX_MANAGE_NAME[*]}; do
            if [[ "$node" != "$LEADER_NAME" ]] ; then
                echo "### SSH: Calling to $node (del-node) ###"
                ssh "$SSHOPTS" "root@$node" "$SCRIPTNAME -a del-node"
            fi
        done;
        del_cluster
    else
        echo "Action must be executed on leader host! '$MANAGE_HOST' vs '$LEADER_NAME'"
    fi
}
status_cluster() {
    ceph -s
}
status_pools() {
    pveceph pool ls
}
status_disks() {
    lsblk
}


# Read arrays
read_osdlist
read_nodes_from_config

# Choose action
case "$ACTION" in
    "ceph-install")
        ceph_install
        ;;
    "add-cluster")
        add_cluster
        ;;
    "del-cluster")
        del_cluster
        ;;
    "add-node")
        add_node
        ;;
    "del-node")
        del_node
        ;;
    "add-all-osd")
        [[ -z "$ENTITY_LIST" ]] && echo "No entities specified" && usage && exit 1
        add_all_osd
        ;;
    "del-all-osd")
        [[ -z "$ENTITY_LIST" ]] && echo "No entities specified" && usage && exit 1
        del_all_osd
        ;;
    "add-osd")
        [[ -z "$ENTITY_NAME" && -z "$ENTITY_LIST" ]] && echo "No entities specified" && usage && exit 1
        add_osd
        ;;
    "del-osd")
        [[ -z "$ENTITY_NAME" && -z "$ENTITY_LIST" ]] && echo "No entities specified" && usage && exit 1
        del_osd
        ;;
    "add-rbd")
        [[ -z "$ENTITY_NAME" ]] && echo "No name specified" && usage && exit 1
        [[ -z "$ENTITY_SIZE" ]] && echo "No size specified" && usage && exit 1
        add_rbd
        ;;
    "del-rbd")
        [[ -z "$ENTITY_NAME" ]] && echo "No name specified" && usage && exit 1
        del_rbd
        ;;
    "add-fs")
        [[ -z "$ENTITY_NAME" ]] && echo "No name specified" && usage && exit 1
        [[ -z "$ENTITY_SIZE" ]] && echo "No size specified" && usage && exit 1
        add_fs
        ;;
    "del-fs")
        [[ -z "$ENTITY_NAME" ]] && echo "No name specified" && usage && exit 1
        del_fs
        ;;
    "bootstrap-cluster")
        bootstrap_cluster
        ;;
    "wipe-cluster")
        wipe_cluster
        ;;
    "status-cluster")
        status_cluster
        ;;
    "status-pools")
        status_pools
        ;;
    "status-disks")
        status_disks
        ;;
    *)
        usage
        echo "Invalid target: '$1'"
        ;;
esac
echo "-------------------------------------------------------------"
echo ""

