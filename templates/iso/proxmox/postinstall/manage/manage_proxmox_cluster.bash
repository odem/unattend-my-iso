#!/bin/bash
# shellcheck disable=SC1090,2005,2029,2048

ACTION=""
CLUSTER_NAME=""
NODE_NAME=""
USERPASS=""
PRIO_0=""
PRIO_1=""
PRIO_2=""
DEFAULT_VOTES_EXPECTED=2
TEMP_VOTES_EXPECTED=1

# Environment variables
POSTINST_PATH=/opt/umi/postinstall
cd "$POSTINST_PATH" || exit 1
envfile=../config/env.bash
if [[ -f "$envfile" ]]; then
    # shellcheck disable=SC1090
    source "$envfile"
fi
LEADER_NAME=$DEFAULT_LEADER_PROXMOX
SSHOPTS="-o StrictHostKeyChecking=no"
MEMBERS_PROX_MANAGE_NAME=()
SCRIPTNAME=/opt/umi/postinstall/manage/manage_proxmox_cluster.bash
VERBOSE=0
usage() {
    echo "      "
    echo "Usage: $0 ACTION [ PARAM1 PARAM2 ... ]"
    echo "      "
    echo "    Actions:"
    echo "      -a bootstrap-cluster  : Creates cluster and adds all nodes"
    echo "      -a wipe-cluster       : Remove all nodes and deletes cluster"
    echo "      -a create-cluster     : Initialize new cluster"
    echo "      -a remove-cluster     : Removes cluster (Must not contain nodes)"
    echo "      -a add-node           : Joins node into cluster"
    echo "      -a remove-node        : Removes node from cluster"
    echo "      -a clean-cluster-info : Forcefully removes corosync config"
    echo "      "
    echo "    Parameters:"
    echo "      -n Cluster_Name       : MY_CLUSTER_NAME"
    echo "      -N Node_Name          : NODE_NAME (No IP! MUST be hostname!)"
    echo "      -L Leader_Name        : LEADER_NAME (No IP! MUST be hostname!)"
    echo "      -P Password           : Needed only for add-node action"
    echo "      -0 Link0 Prio         : SOME_PRIO (INTEGER)"
    echo "      -1 Link1 Prio         : SOME_PRIO (INTEGER)"
    echo "      -2 Link2 Prio         : SOME_PRIO (INTEGER)"
    echo "      "
}
while getopts "a:n:N:L:P:0:1:2:h v " o; do
    [[ $VERBOSE -eq 1 ]] && echo "Processing option: -$o with value: ${OPTARG}"
    case "$o" in
        a)
            ACTION=${OPTARG}
            ;;
        n)
            CLUSTER_NAME=${OPTARG}
            ;;
        N)
            NODE_NAME=${OPTARG}
            ;;
        L)
            LEADER_NAME=${OPTARG}
            ;;
        P)
            USERPASS=${OPTARG}
            ;;
        0)
            PRIO_0=${OPTARG}
            ;;
        1)
            PRIO_1=${OPTARG}
            ;;
        2)
            PRIO_2=${OPTARG}
            ;;
        v)
            VERBOSE=1
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

compare_host2leader() {
    if [[ "$MANAGE_HOST" != "$LEADER_NAME" ]] ; then
        return 1
    else
        return 0
    fi
}
compare_host2node() {
    if [[ "$MANAGE_HOST" != "$NODE_NAME" ]] ; then
        return 1
    else
        return 0
    fi
}
get_host_count() {
    echo "$(pvecm status 2>/dev/null | grep -c "^0x00" 2>/dev/null)"
}
is_host_clustered() {
    echo "$(pvecm nodes 2>/dev/null | grep -c "$MANAGE_HOST" 2>/dev/null)"
}
update_expected_votes() {
    HOST_COUNT=$(get_host_count)
    if [[ $HOST_COUNT -le $DEFAULT_VOTES_EXPECTED ]] ; then
        echo "Adjusting quorum to $TEMP_VOTES_EXPECTED"
        pvecm expected "$TEMP_VOTES_EXPECTED"
    else
        echo "Adjusting quorum to $DEFAULT_VOTES_EXPECTED"
        pvecm expected "$DEFAULT_VOTES_EXPECTED"
    fi
    sleep 1
}
create_link_string() {
    if [[ "$PRIO_0" != "" || "$PRIO_1" != "" || "$PRIO_2" != "" ]] ; then
        FULL_STR=""
        if [[ "$PRIO_0" != "" ]] ; then
            FULL_STR="$FULL_STR --link0 $HB_IP,priority=$PRIO_0"
        fi
        if [[ "$PRIO_1" != "" ]] ; then
            FULL_STR="$FULL_STR --link1 $STORAGE_IP,priority=$PRIO_1"
        fi
        if [[ "$PRIO_2" != "" ]] ; then
            FULL_STR="$FULL_STR --link2 $MANAGE_IP,priority=$PRIO_2"
        fi
        echo "$FULL_STR"
    else
        echo "--link0 $HB_IP  --link1 $STORAGE_IP --link2 $MANAGE_IP" 
    fi
}
read_nodes_from_config() {
    echo "Reading nodes from config..."
    if [[ "$NODES_PROX_MANAGE_NAME" != "" ]]; then
        IFS=',' read -ra CLUSTER_MEMBERS_MANAGE_NAME <<< "$NODES_PROX_MANAGE_NAME"
        echo "${#MEMBERS_PROX_MANAGE_NAME[*]} configured cluster Members: ${MEMBERS_PROX_MANAGE_NAME[*]}"
    fi
}

add_cluster() {
    echo "--- Create Cluster ------------------------------------------"
    echo "=> Trying to create cluster '$CLUSTER_NAME' via $MANAGE_HOST"
    [[ $VERBOSE -eq 1 ]] && pvecm status
    HOST_COUNT=$(get_host_count)
    compare_host2leader
    HOST_CHECK=$?
    if [[ $HOST_CHECK -eq 0 ]] ; then
        clean_cluster_info
	[[ -d /etc/corosync ]] || mkdir /etc/corosync
        systemctl restart corosync
        LINKS=$(create_link_string)
        [[ $VERBOSE -eq 1 ]] && echo "Added Links: $LINKS"
        # shellcheck disable=SC2086
        pvecm create "$CLUSTER_NAME" $LINKS
        echo "Sucess! Cluster created!"
    else
        echo "Error! Hostname unequal to leader name."
    fi
}
del_cluster() {
    echo "--- Remove Cluster ------------------------------------------"
    echo "=> Trying to remove current cluster via $MANAGE_HOST"
    [[ $VERBOSE -eq 1 ]] && pvecm status
    HOST_COUNT=$(get_host_count)
    compare_host2leader
    HOST_CHECK=$?
    if [[ $HOST_CHECK -eq 0 ]] ; then
        if [[ $HOST_COUNT -le 1 ]] ; then
            clean_cluster_info
            echo "Sucess! Cluster removed!"
        else
            [[ $VERBOSE -eq 1 ]] && pvecm nodes
            printf "\nError! Can not remove cluster with more than one node\n"
        fi
    else
        echo "Skipped! Hostname unequal to leader name."
    fi
}

add_node() {
    echo "--- Joining Cluster -----------------------------------------"
    echo "=> Trying to join $MANAGE_HOST via $LEADER_NAME"
    [[ $VERBOSE -eq 1 ]] && pvecm nodes
    HOST_COUNT=$(get_host_count)
    IS_MEMBER=$(is_host_clustered)
    compare_host2leader
    HOST_CHECK=$?
    if [[ $HOST_CHECK -eq 1 ]] ; then
        if [[ $IS_MEMBER -eq 1 ]] ; then
            ssh "$SSHOPTS" root@"$LEADER_NAME" "pvecm delnode $MANAGE_HOST"
            echo "Sleeping after delete"
        fi
        clean_cluster_info
        update_expected_votes
        LINKS=$(create_link_string)
        [[ $VERBOSE -eq 1 ]] && echo "Added Links: $LINKS"
        # shellcheck disable=SC2086
        printf "%s\nyes" "$USERPASS" | pvecm add "$LEADER_NAME" $LINKS
        update_expected_votes
        echo "Sucess! Node joined!"
    else
        echo "Skipped! Leader does not need to be joined!"
    fi
}
del_node() {
    echo "--- Remove Node ---------------------------------------------"
    echo "=> Trying to remove node $NODE_NAME via $MANAGE_HOST"
    [[ $VERBOSE -eq 1 ]] && pvecm nodes
    HOST_COUNT=$(get_host_count)
    IS_MEMBER=$(is_host_clustered)
    compare_host2node
    HOST_CHECK=$?
    if [[ $HOST_CHECK -eq 1 ]] ; then
        if [[ $HOST_COUNT -gt 1 ]] ; then
            if [[ $IS_MEMBER -eq 1 ]] ; then
                ssh "$SSHOPTS" root@"$NODE_NAME" \
                    "$SCRIPTNAME -a clean-cluster-info"
                update_expected_votes
                pvecm delnode "$NODE_NAME"
                update_expected_votes
                echo "Sucess! Node removed!"
            else
                echo "Skipped! Node is not a member of the current cluster"
            fi
        else
            echo "Skipped! Not enough hosts in cluster ($HOST_COUNT)"
        fi
    else
        echo "Skipped! Host name equal to node name."
    fi
}

bootstrap_cluster() {
    echo "--- Bootstrap Cluster ---------------------------------------"
    echo "=> Trying to bootstrap via $MANAGE_HOST"
    [[ $VERBOSE -eq 1 ]] && pvecm nodes
    HOST_COUNT=$(get_host_count)
    IS_MEMBER=$(is_host_clustered)
    compare_host2leader
    HOST_CHECK=$?
    if [[ $HOST_CHECK -eq 0 ]] ; then
        if [[ $HOST_COUNT -eq 0 ]] ; then
            if [[ $IS_MEMBER -eq 0 ]] ; then
                add_cluster
                for node in ${MEMBERS_PROX_MANAGE_NAME[*]}; do
                    ssh "$SSHOPTS" "root@$node" "$SCRIPTNAME -a add-node -L $MANAGE_HOST -N $node"
                done;
            else
                echo "Skipped! Node is not a member of the current cluster"
            fi
        else
            echo "Skipped! Cluster still exists: $HOST_COUNT"
        fi
    else
        echo "Skipped! Host name not equal to leader name: $MANAGE_HOST $LEADER_NAME"
    fi
}
wipe_cluster() {
    echo "--- Wipe Cluster --------------------------------------------"
    echo "=> Trying to wipe cluster via $MANAGE_HOST"
    [[ $VERBOSE -eq 1 ]] && pvecm nodes
    HOST_COUNT=$(get_host_count)
    IS_MEMBER=$(is_host_clustered)
    compare_host2leader
    HOST_CHECK=$?
    if [[ $HOST_CHECK -eq 0 ]] ; then
        for node in ${MEMBERS_PROX_MANAGE_NAME[*]}; do
            NODE_NAME=$node
            del_node
        done;
        del_cluster
    else
        echo "Skipped! Host name not equal to leader name."
    fi
}

clean_cluster_info() {
    # To delete in-use corosync configs, 
    # we need to run proxmox via the cluster filesystem utility
    # Link: https://pve.proxmox.com/wiki/Cluster_Manager#_remove_a_cluster_node
    echo "--- Wiping cluster info -------------------------------------"
    echo "=> Removing corosync configs via $MANAGE_HOST"
    systemctl stop pve-cluster corosync
    pmxcfs -l
    rm /etc/corosync/* >/dev/null 2>&1
    rm /etc/pve/corosync.conf >/dev/null 2>&1
    killall pmxcfs
    mkdir -p /etc/corosync
    systemctl start pve-cluster corosync
    echo "Sucess! Cluster info wiped!"
}
status_cluster() {
    pvecm status
}

read_nodes_from_config
case "$ACTION" in
    "add-cluster")
        [[ -z "$CLUSTER_NAME" ]] && echo "No cluster name" && usage && exit 1
        add_cluster
        ;;
    "del-cluster")
        del_cluster
        ;;
    "add-node")
        [[ -z "$USERPASS" ]] && USERPASS="$CFG_USER_ROOT_PASSWORD"
        [[ -z "$USERPASS" ]] && echo "No password" && usage && exit 1
        add_node
        ;;
    "del-node")
        [[ -z "$NODE_NAME" ]] && echo "No node name " && usage && exit 1
        del_node
        ;;
    "bootstrap-cluster")
        [[ -z "$CLUSTER_NAME" ]] && echo "No cluster name" && usage && exit 1
        bootstrap_cluster
        ;;
    "wipe-cluster")
        wipe_cluster
        ;;
    "status")
        status_cluster
        ;;
    "clean-cluster-info")
        clean_cluster_info
        ;;
    *)
        usage
        echo "Invalid target: '$1'"
        ;;
esac
echo "-------------------------------------------------------------"
echo ""

