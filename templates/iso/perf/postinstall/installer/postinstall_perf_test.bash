#!/bin/bash
echo "#########################################################################"
echo "# Unattend-My-Iso: SYSTEMD TARGET PERF_SIMPLE"
echo "#########################################################################"

RESULT_DIR=./tester
export DEBIAN_FRONTEND=noninteractive
SLEEP_BEFORE=1
SLEEP_BETWEEN=1
SLEEP_AFTER=1
MAX_LOOPS=1000
FIO_SIZE=256
FIO_LOOPS=5

# Clean
rm -rf $RESULT_DIR #2>/dev/null
mkdir -p $RESULT_DIR #2>/dev/null
pkill "$(which fio)"

# Iterate loops
sleep "$SLEEP_BEFORE"
for counter in $(seq 1 "$MAX_LOOPS"); do
    echo "---------------------------------------------------------------------"
    echo "- Perftest \$counter"
    echo "---------------------------------------------------------------------"
    fio --loops="$FIO_LOOPS" --size="${FIO_SIZE}m" --filename="$RESULT_DIR/.fiomark.tmp" \
      --stonewall --ioengine=libaio --direct=1 --zero_buffers=0 --output-format=json \
      --name=Seqread --bs="${FIO_SIZE}m" --iodepth=1 --numjobs=1 --rw=read \
      --name=Seqwrite --bs="${FIO_SIZE}m" --iodepth=1 --numjobs=1 --rw=write \
      > $RESULT_DIR/perftest.log
    echo "DONE"
    ls -la "$RESULT_DIR"
    cat $RESULT_DIR/perftest.log

    sleep "$SLEEP_BETWEEN"
    QUERY='def read_bw(name): [.jobs[] | select(.jobname==name+"read").read.bw] | add / 1024 | floor;
       def read_iops(name): [.jobs[] | select(.jobname==name+"read").read.iops] | add | floor;
       def write_bw(name): [.jobs[] | select(.jobname==name+"write").write.bw] | add / 1024 | floor;
       def write_iops(name): [.jobs[] | select(.jobname==name+"write").write.iops] | add | floor;
       def job_summary(name): read_bw(name), read_iops(name), write_bw(name), write_iops(name);
       job_summary("Seq")'
    read -d '\n' -ra V <<< "$(jq "$QUERY" "$RESULT_DIR/perftest.log")"
    echo -e "
    Results:
    \033[0;33m
    Sequential Read: ${V[0]}MB/s
    Sequential Write: ${V[2]}MB/s
    \033[0;32m
    "
    mv $RESULT_DIR/perftest.log $RESULT_DIR/result_\$counter.json
done
sleep "$SLEEP_AFTER"
echo "Done"
exit 0

