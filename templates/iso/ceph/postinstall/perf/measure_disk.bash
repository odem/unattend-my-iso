#!/bin/bash

RAMDISK="/mnt/ramdisk"
TESTNAME="noname"
METHOD="raw"
OUTDIR="tests/latest"
DEST_DIR=$OUTDIR
INPUT_SIZE=1024
ITERATIONS=2
DEFAULT_SIZES=(128 512 1024 2048 4096)
PLOT_LATEST=0
INSTALL_TOOLS=0
CLEAR_CACHE=0
TEST_DISKS=0

BLOCKSIZE="4K"
FIO_RUNTIME=60
FIO_DIRECT=1
FIO_IODEPTH=1
FIO_FSYNC=1
FIO_JOBS=1
FIO_RAND=""
FIO_ENGINE=libaio
FIO_RAMPTIME="2s"

SCRIPT_PATH="$(dirname "$(realpath "$0")")"
export LC_ALL="C"

usage() {
    echo "      " 1>&2
    echo "Usage: $0 [ PARAM1 PARAM2 ... ] [ FLAG1 FLAG2 ... ]" 1>&2
    echo "      " 1>&2
    echo "    Parameters:" 1>&2
    echo "      -s Testsize           : DEFAULT_LIST with size 0" 1>&2
    echo "      -d Destination dir    : Target dir" 1>&2
    echo "      -n Test name          : Name of the test" 1>&2
    echo "      -i Iterations         : Number of iterations" 1>&2
    echo "      -f fio runtime        : time in seconds" 1>&2
    echo "      -b block size         : SIZE+UNIT => INT+[K|M], e.g. 1M" 1>&2
    echo "      -m Method             : all,raw,fio" 1>&2
    echo "      " 1>&2
    echo "    Flags:" 1>&2
    echo "      -C                    : Clear cache before each test" 1>&2
    echo "      -I                    : Install tools" 1>&2
    echo "      " 1>&2
}
while getopts "I C T P h s:b:d:i:n:m:f:" o; do
    case "$o" in
        s)
            INPUT_SIZE=${OPTARG}
            ;;
        b)
            BLOCKSIZE=${OPTARG}
            ;;
        d)
            DEST_DIR=${OPTARG}
            ;;
        n)
            TESTNAME=${OPTARG}
            ;;
        i)
            ITERATIONS=${OPTARG}
            ;;
        f)
            FIO_RUNTIME=${OPTARG}
            ;;
        m)
            METHOD=${OPTARG}
            ;;
        C)
            CLEAR_CACHE=1
            ;;
        I)
            INSTALL_TOOLS=1
            ;;
        P)
            PLOT_LATEST=1
            ;;
        T)
            TEST_DISKS=1
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

TESTFILE="$OUTDIR/test-latest.csv"
TESTFILE_NC_FIO_READ="$OUTDIR/test-latest-1-cfs-fio-read.csv"
TESTFILE_NC_FIO_WRITE="$OUTDIR/test-latest-1-cfs-fio-write.csv"
TESTFILE_NC_RAW_READ="$OUTDIR/test-latest-1-cfs-raw-read.csv"
TESTFILE_NC_RAW_WRITE="$OUTDIR/test-latest-1-cfs-raw-write.csv"
TESTFILE_WC_FIO_READ="$OUTDIR/test-latest-0-cfs-fio-read.csv"
TESTFILE_WC_FIO_WRITE="$OUTDIR/test-latest-0-cfs-fio-write.csv"
TESTFILE_WC_RAW_READ="$OUTDIR/test-latest-0-cfs-raw-read.csv"
TESTFILE_WC_RAW_WRITE="$OUTDIR/test-latest-0-cfs-raw-write.csv"
SOURCE_FILE="${INPUT_SIZE}_mb"
DEST_FILE="${DEST_DIR}/$SOURCE_FILE"
SIZE_MB=$INPUT_SIZE

install_tools() {
    if [[ $INSTALL_TOOLS -eq 1 ]] ; then
        sudo apt -y install bc gnuplot fio
    fi
}
prepare() {
    if [[ ! -d $RAMDISK ]]; then
        sudo mkdir -p "$RAMDISK"
        sudo mount -t tmpfs -o size=12G tmpfs "$RAMDISK"
        sudo chmod a+rw -R "$RAMDISK"
    fi
    if [[ ! -d $OUTDIR ]]; then
        mkdir -p "$OUTDIR"
    fi
    if [[ ! -d $DEST_DIR ]]; then
        mkdir -p "$DEST_DIR"
    fi
    if [ ! -f "$TESTFILE" ]; then
      echo "DATE,TIME,CLEAR_CACHE,TESTMETHOD,SIZE,ITERATION,ELAPSED_MS,ELAPSED_S,RATE,TESTNAME,DESTINATION,ACCESS" \
          > "$TESTFILE"
    fi
    dd if=/dev/urandom of="$RAMDISK/$SOURCE_FILE" bs="$BLOCKSIZE" count="$SIZE_MB" status=progress 2>/dev/null >/dev/null 
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create the write-file."
        exit 1
    fi
    sync
}
clear_cache() {
    if [[ $CLEAR_CACHE -eq 1 ]] ; then
        sync && echo 3 | sudo tee /proc/sys/vm/drop_caches 2>/dev/null >/dev/null
    fi
}
test_raw_read() {
  sync
  clear_cache
  start_time=$(date +%s%3N)
  dd if="$DEST_DIR/$SOURCE_FILE" of=/dev/zero bs="$BLOCKSIZE" >/dev/null 2>&1 
  if [ $? -ne 0 ]; then
      echo "Error: Read operation failed."
      exit 1
  fi
  end_time=$(date +%s%3N)
  elapsed_ms=$((end_time - start_time))
  elapsed_sec=$(echo "scale=3; ${elapsed_ms} / 1000" | bc)
  transfer_rate=$(echo "scale=0; ${SIZE_MB} / ${elapsed_sec}" | bc)
  elapsed_sec=$(echo "$elapsed_sec" | sed 's/^\./0\./')
  rm -f "$DEST_FILE"
  echo "$elapsed_ms" "$elapsed_sec" "$transfer_rate"
  return 0
}
test_raw_write() {
  sync
  clear_cache
  start_time=$(date +%s%3N)
  dd if="$RAMDISK/$SOURCE_FILE" of="$DEST_FILE" conv=fdatasync bs="$BLOCKSIZE" >/dev/null 2>&1
  if [ $? -ne 0 ]; then
      echo "Error: Write operation failed."
      exit 1
  fi
  sync
  sync
  end_time=$(date +%s%3N)
  elapsed_ms=$((end_time - start_time))
  elapsed_sec=$(echo "scale=3; ${elapsed_ms} / 1000" | bc)
  transfer_rate=$(echo "scale=0; ${SIZE_MB} / ${elapsed_sec}" | bc)
  elapsed_sec=$(echo "$elapsed_sec" | sed 's/^\./0\./')
  if [ $? -ne 0 ]; then
      echo "Warning: Failed to delete the write-file."
      return 1
  fi
  echo "$elapsed_ms" "$elapsed_sec" "$transfer_rate"
  return 0
}

test_fio_read() {
  sync
  clear_cache
  FIO_TYPE="read"
  READSPEED=$(fio --name="$TESTNAME" \
      --ioengine=$FIO_ENGINE \
      --direct=$FIO_DIRECT \
      --ramp_time="$FIO_RAMPTIME" \
      --time_based \
      --bs="$BLOCKSIZE" \
      --iodepth=$FIO_IODEPTH \
      --sync=$FIO_FSYNC \
      --runtime="$FIO_RUNTIME" \
      --filename="$DEST_DIR/$SOURCE_FILE" \
      --size="${SIZE_MB}"MB \
      --numjobs=$FIO_JOBS \
      --rw="${FIO_RAND}${FIO_TYPE}" | grep " READ: " \
      | cut -d " " -f 6 | tr -d "()MB/s,")
  sync
  sync
  if [ $? -ne 0 ]; then
      echo "Error: Copy operation failed."
      exit 1
  fi
  transfer_rate=$READSPEED
  UNIT_KB=$(echo "$transfer_rate" | grep -c "k")
    if [[ "$UNIT_KB" == "1" ]]; then
        transfer_rate="0."$(echo "$READSPEED" | tr -d "ki")
    fi
  elapsed_ms=$(echo "scale=6; ${SIZE_MB} / ${transfer_rate} * 1000" | bc)
  elapsed_ms=$(echo "scale=0; ${elapsed_ms} / 1" | bc)
  elapsed_sec=$(echo "scale=3; ${elapsed_ms} / 1000" | bc)
  elapsed_sec=$(echo "$elapsed_sec" | sed 's/^\./0\./')
  rm -f "$DEST_FILE"
  if [ $? -ne 0 ]; then
      echo "Warning: Failed to delete the read-file."
      return 1
  fi
  echo "$elapsed_ms" "$elapsed_sec" "$transfer_rate"
  return 0
}
test_fio_write() {
  sync
  clear_cache
  FIO_TYPE="write"
  WRITESPEED=$(fio --name="$TESTNAME" \
      --ioengine=$FIO_ENGINE \
      --direct=$FIO_DIRECT \
      --ramp_time="$FIO_RAMPTIME" \
      --time_based \
      --bs="$BLOCKSIZE" \
      --iodepth=$FIO_IODEPTH \
      --sync=$FIO_FSYNC \
      --runtime="$FIO_RUNTIME" \
      --filename="$DEST_FILE" \
      --size="${SIZE_MB}"MB \
      --numjobs=$FIO_JOBS \
      --rw="${FIO_RAND}${FIO_TYPE}" | grep " WRITE: " \
      | cut -d " " -f 5 | tr -d "()MB/s,")
  sync
  sync
  if [ $? -ne 0 ]; then
      echo "Error: Copy operation failed."
      exit 1
  fi
  transfer_rate=$WRITESPEED
  UNIT_KB=$(echo "$transfer_rate" | grep -c "k")
    if [[ "$UNIT_KB" == "1" ]]; then
        transfer_rate="0."$(echo "$WRITESPEED" | tr -d "k")
    fi
  elapsed_ms=$(echo "scale=6; ${SIZE_MB} / ${transfer_rate} * 1000" | bc)
  elapsed_ms=$(echo "scale=0; ${elapsed_ms} / 1" | bc)
  elapsed_sec=$(echo "scale=3; ${elapsed_ms} / 1000" | bc)
  elapsed_sec=$(echo "$elapsed_sec" | sed 's/^\./0\./')
  rm -f "$DEST_FILE"
  if [ $? -ne 0 ]; then
      echo "Warning: Failed to delete the write-file."
      return 1
  fi
  echo "$elapsed_ms" "$elapsed_sec" "$transfer_rate"
  return 0
}
update_results() {
    RUNTIME_MS=$(printf "%5.3f" "$5")
    RUNTIME_SEC=$(echo "$6" | sed 's/^\./0\./')
    RUNTIME_SEC=$(printf "%5.3f" "$RUNTIME_SEC")
    TP=$(printf "%5.3f" "$7")
    NAME=$(printf "%s-%d" "$8" "$3")
    if [[ "$METHOD" == "fio" ]] ; then
        printf "%-30s (%3d) CFS : %5s-%-3s via %3s for %7.3f s => %8.1f MB/sec\n" "$NAME" "$4" "${10}" "${11}" "$METHOD" "$RUNTIME_SEC" "$TP"
    elif [[ "$METHOD" == "raw" ]] ; then
        printf "%-30s (%3d) CFS : %5s-%-3s via %3s for %7.3f s => %8.1f MB/sec\n" "$NAME" "$4" "${10}" "${11}" "$METHOD" "$RUNTIME_SEC" "$TP"
    fi
    TEXTLINE="$(date +'%Y-%m-%d,%H:%M:%S'),$1,$2,$3,$4,$RUNTIME_MS,$RUNTIME_SEC,$TP,$8,$9,${10},${11}"
    echo "$TEXTLINE" >> "$TESTFILE"
}
plot_results() {
    if [[ $PLOT_LATEST  -eq 1 ]] ; then
        if [[ $CLEAR_CACHE -eq 1 ]]; then
            if [[ "$METHOD" == "all" || "$METHOD" == "fio" ]]; then
                cat "$TESTFILE" | grep ",1,fio,"  | grep ",read," | sort -t, -n -k5 -k9 > "$TESTFILE_NC_FIO_READ"
                sed "s#Throughput,No-Cache,cfs,fio,read#${DEST_DIR},Throughput,No-Cache,cfs,fio,read#g" "$SCRIPT_PATH"/plot_defaults_nc_cfs_fio_read.gpl | gnuplot
                cat "$TESTFILE" | grep ",1,fio,"  | grep ",write," | sort -t, -n -k5 -k9 > "$TESTFILE_NC_FIO_WRITE"
                sed "s#Throughput,No-Cache,cfs,fio,write#${DEST_DIR},Throughput,No-Cache,cfs,fio,write#g" "$SCRIPT_PATH"/plot_defaults_nc_cfs_fio_write.gpl | gnuplot
            fi
            if [[ "$METHOD" == "all" || "$METHOD" == "raw" ]]; then
                cat "$TESTFILE" | grep ",1,raw,"  | grep ",read," | sort -t, -n -k5 -k9 > "$TESTFILE_NC_RAW_READ"
                sed "s#Throughput,With-Cache,cfs,raw,read#${DEST_DIR},Throughput,No-Cache,cfs,raw,read#g" "$SCRIPT_PATH"/plot_defaults_nc_cfs_raw_read.gpl | gnuplot
                cat "$TESTFILE" | grep ",1,raw," | grep ",write," | sort -t, -n -k5 -k9 > "$TESTFILE_NC_RAW_WRITE"
                sed "s#Throughput,No-Cache,cfs,raw,write#${DEST_DIR},Throughput,No-Cache,cfs,raw,write#g" "$SCRIPT_PATH"/plot_defaults_nc_cfs_raw_write.gpl | gnuplot
            fi
        else
            if [[ "$METHOD" == "all" || "$METHOD" == "fio" ]]; then
                cat "$TESTFILE" | grep ",0,fio," | grep ",read," | sort -t, -n -k5 -k9 > "$TESTFILE_WC_FIO_READ"
                sed "s#Throughput,With-Cache,cfs,fio,read#${DEST_DIR},Throughput,With-Cache,cfs,fio,read#g" "$SCRIPT_PATH"/plot_defaults_wc_cfs_fio_read.gpl | gnuplot
                cat "$TESTFILE" | grep ",0,fio," | grep ",write," | sort -t, -n -k5 -k9 > "$TESTFILE_WC_FIO_WRITE"
                sed "s#Throughput,With-Cache,cfs,fio,write#${DEST_DIR},Throughput,With-Cache,cfs,fio,write#g" "$SCRIPT_PATH"/plot_defaults_wc_cfs_fio_write.gpl | gnuplot
            fi 
            if [[ "$METHOD" == "all" || "$METHOD" == "raw" ]]; then
                cat "$TESTFILE" | grep ",0,raw,"  | grep ",read," | sort -t, -n -k5 -k9 > "$TESTFILE_WC_RAW_READ"
                sed "s#Throughput,With-Cache,raw,read#${DEST_DIR},Throughput,With-Cache,cfs,raw,read#g" "$SCRIPT_PATH"/plot_defaults_wc_cfs_raw_read.gpl | gnuplot
                cat "$TESTFILE" | grep ",0,raw,"  | grep ",write," | sort -t, -n -k5 -k9 > "$TESTFILE_WC_RAW_WRITE"
                sed "s#Throughput,With-Cache,cfs,raw,write#${DEST_DIR},Throughput,With-Cache,cfs,raw,write#g" "$SCRIPT_PATH"/plot_defaults_wc_cfs_raw_write.gpl | gnuplot
            fi
        fi
    fi
}
loop_iterations() {
    prepare
    for (( i=1; i<=ITERATIONS; i++ )); do
        if [[ "$METHOD" == "raw" ]] ; then
            results_write=$(test_raw_write)
            results_read=$(test_raw_read)
        elif [[ "$METHOD" == "fio" ]] ; then
            results_write=$(test_fio_write)
            results_read=$(test_fio_read)
            rm -f "$DEST_FILE"
        fi
      success=$?
      # echo "SUCCESS: $success -> '$results_write'"
      if [[ success -eq 0 ]] ; then
          arr_write=($results_write)
          arr_read=($results_read)
          update_results "$CLEAR_CACHE" "$METHOD" "$SIZE_MB" "$i" \
              "${arr_write[0]}" "${arr_write[1]}" "${arr_write[2]}" \
               "$TESTNAME" "$DEST_FILE" "write" "$BLOCKSIZE"
          update_results "$CLEAR_CACHE" "$METHOD" "$SIZE_MB" "$i" \
              "${arr_read[0]}" "${arr_read[1]}" "${arr_read[2]}" \
               "$TESTNAME" "$DEST_FILE" "read" "$BLOCKSIZE"
      fi
    done
    rm -rf "${RAMDISK}/${SOURCE_FILE}"
    sudo umount "$RAMDISK"
    sudo rm -rf "$RAMDISK"
}
loop_sizes() {
    for num in "${DEFAULT_SIZES[@]}"; do
      SOURCE_FILE="${num}_mb"
      DEST_FILE="${DEST_DIR}/$SOURCE_FILE"
      SIZE_MB=$num
      loop_iterations
    done
    rm -rf "$OUTDIR/$SOURCE_FILE"
}

loop_methods() {
    if [[ $TEST_DISKS -eq 1 ]] ; then
        if [[ "$METHOD" != "all" ]] ; then
            if [[ $INPUT_SIZE -eq 0 ]] ; then
                loop_sizes
            else
                loop_iterations
            fi
        else
            if [[ $INPUT_SIZE -eq 0 ]] ; then
                METHOD="raw"
                loop_sizes
                METHOD="fio"
                loop_sizes
            else
                METHOD="raw"
                loop_iterations
                METHOD="fio"
                loop_iterations
            fi
        fi
    fi
}

install_tools
loop_methods
plot_results

# sudo rm -rf $OUTDIR


