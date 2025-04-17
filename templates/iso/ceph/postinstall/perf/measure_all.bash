#!/bin/bash

# Default Values
SCRIPT_PATH="$(dirname "$(realpath "$0")")"
TESTNAME="foo"
BLOCKSIZE="4K"
METHOD="all"
ITERATIONS=2
FIO_RUNTIME=10
INPUT_SIZE=0
FLAG_DISK=0
FLAG_FS=0
FLAG_RBD=0
FLAG_WARMUP=0

usage() {
    echo "      " 1>&2
    echo "Usage: $0 [ PARAM1 PARAM2 ... ] [ FLAG1 FLAG2 ... ]" 1>&2
    echo "      " 1>&2
    echo "    Parameters:" 1>&2
    echo "      -s Testsize           : DEFAULT_LIST with size 0" 1>&2
    echo "      -n Test name          : Name of the test" 1>&2
    echo "      -i Iterations         : Number of iterations" 1>&2
    echo "      -f fio runtime        : time in seconds" 1>&2
    echo "      -b block size         : SIZE+UNIT => INT+[K|M], e.g. 1M" 1>&2
    echo "      -m Method             : all,raw,fio" 1>&2
    echo "      " 1>&2
    echo "    Flags:" 1>&2
    echo "      -D                    : Test host disk" 1>&2
    echo "      -F                    : Test filesystems" 1>&2
    echo "      -R                    : Test rbd pools" 1>&2
    echo "      -W                    : Warmup" 1>&2
    echo "      " 1>&2
}

while getopts "h D F R W s:b:i:n:f:m:" o; do
    case "$o" in
        s)
            INPUT_SIZE=${OPTARG}
            ;;
        b)
            BLOCKSIZE=${OPTARG}
            ;;
        n)
            TESTNAME=${OPTARG}
            ;;
        m)
            METHOD=${OPTARG}
            ;;
        i)
            ITERATIONS=${OPTARG}
            ;;
        f)
            FIO_RUNTIME=${OPTARG}
            ;;
        D)
            FLAG_DISK=1
            ;;
        F)
            FLAG_FS=1
            ;;
        R)
            FLAG_RBD=1
            ;;
        W)
            FLAG_WARMUP=1
            ;;
        h)
            usage
            exit 0
            ;;
        *)
            echo "Unknown parameter $o with '${OPTARG}'"
            usage
            ;;
    esac
done
shift $((OPTIND-1))

test_rbd_pool() {
    POOLNAME=$1
    FULLNAME=${TESTNAME}-$POOLNAME
    PREFIX="rbd"
    echo "--- Test $FULLNAME---------------------------------------------------"
    "$SCRIPT_PATH"/measure_rbd.bash -T -C -m "$METHOD" -b "$BLOCKSIZE" -i "$ITERATIONS" -f "$FIO_RUNTIME" -s "$INPUT_SIZE" -n "rbd-nc-$FULLNAME" -d "$POOLNAME"
    "$SCRIPT_PATH"/measure_rbd.bash -T -m "$METHOD" -b "$BLOCKSIZE" -i "$ITERATIONS" -f "$FIO_RUNTIME" -s "$INPUT_SIZE" -n "rbd-wc-$FULLNAME" -d "$POOLNAME"
    "$SCRIPT_PATH"/measure_rbd.bash -P -C -m "$METHOD" -b "$BLOCKSIZE" -n "rbd-nc-$FULLNAME" -d "$POOLNAME"
    "$SCRIPT_PATH"/measure_rbd.bash -P -m "$METHOD" -b "$BLOCKSIZE" -n "rbd-wc-$FULLNAME" -d "$POOLNAME"
    rm -rf "tests/$PREFIX-$FULLNAME"
    mkdir -p "tests/$PREFIX-$FULLNAME"
    cp tests/latest/*.csv tests/latest/*.pdf "tests/$PREFIX-$FULLNAME" >/dev/null 2>&1
    sudo rm -rf tests/latest
    sync && sync && sleep 5
}

test_cfs_folder() {
    POOLNAME=$1
    FULLNAME=${TESTNAME}-$POOLNAME
    PREFIX="cfs"
    echo "--- Test $FULLNAME---------------------------------------------------"
    "$SCRIPT_PATH"/measure_cfs.bash -T -C -m "$METHOD" -b "$BLOCKSIZE" -i "$ITERATIONS" -f "$FIO_RUNTIME" -s "$INPUT_SIZE" -n "cfs-nc-$FULLNAME" -d "/mnt/$POOLNAME/test-nc-$FULLNAME"
    "$SCRIPT_PATH"/measure_cfs.bash -T -m "$METHOD" -b "$BLOCKSIZE" -i "$ITERATIONS" -f "$FIO_RUNTIME" -s "$INPUT_SIZE" -n "cfs-wc-$FULLNAME" -d "/mnt/$POOLNAME/test-wc-$FULLNAME"
    "$SCRIPT_PATH"/measure_cfs.bash -P -C -m "$METHOD" -b "$BLOCKSIZE" -n "cfs-nc-$FULLNAME" -d /mnt/"$POOLNAME/test-nc-$FULLNAME"
    "$SCRIPT_PATH"/measure_cfs.bash -P -m "$METHOD" -b "$BLOCKSIZE" -n "cfs-wc-$FULLNAME" -d /mnt/"$POOLNAME/test-wc-$FULLNAME"
    rm -rf "tests/$PREFIX-$FULLNAME"
    mkdir -p "tests/$PREFIX-$FULLNAME"
    cp tests/latest/*.csv tests/latest/*.pdf "tests/$PREFIX-$FULLNAME" >/dev/null 2>&1
    sudo rm -rf tests/latest
    sync && sync && sleep 5
}

test_folder() {
    DIRNAME=$1
    FULLNAME=${TESTNAME}-hostdisk
    PREFIX="hostdisk"
    echo "--- Test $FULLNAME---------------------------------------------------"
    "$SCRIPT_PATH"/measure_cfs.bash -T -C -m "$METHOD" -b "$BLOCKSIZE" -i "$ITERATIONS" -f "$FIO_RUNTIME" -s "$INPUT_SIZE" -n "test-nc-$FULLNAME" -d "$DEST_DIR/$DIRNAME"
    "$SCRIPT_PATH"/measure_cfs.bash -T -m "$METHOD" -b "$BLOCKSIZE" -i "$ITERATIONS" -f "$FIO_RUNTIME" -s "$INPUT_SIZE" -n "test-wc-$FULLNAME" -d "$DEST_DIR/$DIRNAME"
    "$SCRIPT_PATH"/measure_cfs.bash -P -C -m "$METHOD" -b "$BLOCKSIZE" -n "test-nc-$FULLNAME" -d "$DEST_DIR/$DIRNAME"
    "$SCRIPT_PATH"/measure_cfs.bash -P -m "$METHOD" -b "$BLOCKSIZE" -n "test-wc-$FULLNAME" -d "$DEST_DIR/$DIRNAME"
    rm -rf "tests/$PREFIX-$FULLNAME"
    mkdir -p "tests/$PREFIX-$FULLNAME"
    cp tests/latest/*.csv tests/latest/*.pdf "tests/$PREFIX-$FULLNAME" >/dev/null 2>&1
    sudo rm -rf tests/latest
    sync && sync && sleep 5

}

warmup() {
    sync && sync
    if [[ $FLAG_WARMUP -eq 1 ]]; then
        "$SCRIPT_PATH"/measure_cfs.bash -T -C -m raw -b "$BLOCKSIZE" -i 1 -f 1 -s 0 -n warmup -d /tmp/warmup
        sudo rm -rf tests/lates >/dev/null 2>&1t
        sync && sync && sleep 5
    fi
}

# warmup
warmup

# Measure Begin
start_time=$(date +%s%3N)

# Tests
echo "--- $start_time ---------------------------------------------------------"
if [[ $FLAG_DISK -eq 1 ]]; then
    test_folder "/tmp/disk"
fi
if [[ $FLAG_FS -eq 1 ]]; then
    test_cfs_folder "nhc-foo3-fs"
    test_cfs_folder "nhc-foo21-fs"
    test_cfs_folder "nhc-foo31-fs"
fi
if [[ $FLAG_RBD -eq 1 ]]; then
    test_rbd_pool "nhc-rbd-rep2"
    test_rbd_pool "nhc-rbd-rep3"
    test_rbd_pool "nhc-rbd-rep4"
fi
end_time=$(date +%s%3N)
echo "--- $end_time ---------------------------------------------------------"

# Measure end
elapsed_ms=$((end_time - start_time))
elapsed_sec=$(echo "scale=3; ${elapsed_ms} / 1000" | bc)
elapsed_sec=$(echo "$elapsed_sec" | sed 's/^\./0\./')
echo "Elapsed Time: $elapsed_sec"

