#!/bin/bash

ACTION=""
CLUSTER_NAME=""
NODE_NAME=""
USERPASS=""
PRIO_1=""
PRIO_2=""
PRIO_3=""
DEFAULT_VOTES_EXPECTED=2
TEMP_VOTES_EXPECTED=1
PROXMOX_NET=10.40.1
script_path="$(dirname "$(realpath "$0")")"
source "$script_path"/../hostconfig.env
LEADER_NAME=$PROXMOX_HOST_1
THIRDLINK_IP=$STORAGE_IP
SSHOPTS="-o StrictHostKeyChecking=no"
VERBOSE=0
usage() {
    echo "      " 1>&2
    echo "Usage: $0 ACTION [ PARAM1 PARAM2 ... ]" 1>&2
    echo "      " 1>&2
    echo "    Actions:" 1>&2
    echo "      -a create-cluster     : Initialize new cluster" >&2
    echo "      -a remove-cluster     : Removes cluster (Must not contain nodes)" >&2
    echo "      -a add-node           : Joins node into cluster" >&2
    echo "      -a remove-node        : Removes node from cluster" >&2
    echo "      -a clean-cluster-info : Forcefully removes corosync config" >&2
    echo "      " 1>&2
    echo "    Parameters:" 1>&2
    echo "      -n Cluster_Name       : MY_CLUSTER_NAME" 1>&2
    echo "      -N Node_Name          : NODE_NAME (No IP! MUST be hostname!)" 1>&2
    echo "      -L Leader_Name        : LEADER_NAME (No IP! MUST be hostname!)" 1>&2
    echo "      -P Password           : Needed only for add-node action" 1>&2
    echo "      -0 Link0 Prio         : SOME_PRIO (INTEGER)" 1>&2
    echo "      -1 Link1 Prio         : SOME_PRIO (INTEGER)" 1>&2
    echo "      -2 Link2 Prio         : SOME_PRIO (INTEGER)" 1>&2
    echo "      " 1>&2
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
    if [[ "$PROXMOX_HOST" != "$LEADER_NAME" ]] ; then
        return 1
    else
        return 0
    fi
}
compare_host2node() {
    if [[ "$PROXMOX_HOST" != "$NODE_NAME" ]] ; then
        return 1
    else
        return 0
    fi
}
get_host_count() {
    echo "$(pvecm status 2>/dev/null | grep -c "$PROXMOX_NET" 2>/dev/null)"
}
is_host_clustered() {
    echo "$(pvecm status 2>/dev/null | grep -c "$PROXMOX_IP" 2>/dev/null)"
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
            FULL_STR="$FULL_STR --link2 $PROXMOX_IP,priority=$PRIO_2"
        fi
        echo "$FULL_STR"
    else
        echo "--link0 $HB_IP  --link1 $STORAGE_IP --link2 $PROXMOX_IP" 
    fi
}

create_cluster() {
    echo "--- Create Cluster ------------------------------------------"
    echo "=> Trying to create cluster '$CLUSTER_NAME' via $PROXMOX_HOST"
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
        pvecm create $CLUSTER_NAME $LINKS
        echo "Sucess! Cluster created!"
    else
        echo "Error! Hostname unequal to leader name."
    fi
}
remove_cluster() {
    echo "--- Remove Cluster ------------------------------------------"
    echo "=> Trying to remove current cluster via $PROXMOX_HOST"
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
    echo "=> Trying to join $PROXMOX_HOST via $LEADER_NAME"
    [[ $VERBOSE -eq 1 ]] && pvecm nodes
    HOST_COUNT=$(get_host_count)
    IS_MEMBER=$(is_host_clustered)
    compare_host2leader
    HOST_CHECK=$?
    if [[ $HOST_CHECK -eq 1 ]] ; then
        if [[ $IS_MEMBER -eq 1 ]] ; then
            ssh "$SSHOPTS" root@"$LEADER_NAME" "pvecm delnode $PROXMOX_HOST"
            echo "Sleeping after delete"
        fi
        clean_cluster_info
        update_expected_votes
        LINKS=$(create_link_string)
        [[ $VERBOSE -eq 1 ]] && echo "Added Links: $LINKS"
        printf "$USERPASS\nyes" | pvecm add $LEADER_NAME $LINKS
        update_expected_votes
        echo "Sucess! Node joined!"
    else
        echo "Skipped! Leader does not need to be joined!"
    fi
}
remove_node() {
    echo "--- Remove Node ---------------------------------------------"
    echo "=> Trying to remove node $NODE_NAME via $PROXMOX_HOST"
    [[ $VERBOSE -eq 1 ]] && pvecm nodes
    HOST_COUNT=$(get_host_count)
    IS_MEMBER=$(is_host_clustered)
    compare_host2node
    HOST_CHECK=$?
    if [[ $HOST_CHECK -eq 1 ]] ; then
        if [[ $HOST_COUNT -gt 1 ]] ; then
            if [[ $IS_MEMBER -eq 1 ]] ; then
                ssh "$SSHOPTS" root@"$NODE_NAME" \
                    "/opt/postinstall/manage_cluster.bash -a clean-cluster-info"
                update_expected_votes
                pvecm delnode $NODE_NAME
                update_expected_votes
                echo "Sucess! Node removed!"
                exit 0
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

clean_cluster_info() {
    # To delete in-use corosync configs, 
    # we need to run proxmox via the cluster filesystem utility
    # Link: https://pve.proxmox.com/wiki/Cluster_Manager#_remove_a_cluster_node
    echo "--- Wiping cluster info -------------------------------------"
    echo "=> Removing corosync configs via $PROXMOX_HOST"
    systemctl stop pve-cluster corosync
    pmxcfs -l
    rm /etc/corosync/* >/dev/null 2>&1
    rm /etc/pve/corosync.conf >/dev/null 2>&1
    killall pmxcfs
    mkdir -p /etc/corosync
    systemctl start pve-cluster corosync
    echo "Sucess! Cluster info wiped!"
}

case "$ACTION" in
    "create-cluster")
        [[ -z "$CLUSTER_NAME" ]] && echo "No cluster name" && usage && exit 1
        create_cluster
        ;;
    "remove-cluster")
        remove_cluster
        ;;
    "add-node")
        [[ -z "$USERPASS" ]] && echo "No password" && usage && exit 1
        add_node
        ;;
    "remove-node")
        [[ -z "$NODE_NAME" ]] && echo "No node name " && usage && exit 1
        remove_node
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

