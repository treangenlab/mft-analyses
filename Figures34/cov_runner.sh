#!/bin/bash
set -uo pipefail

BASE=/dodo/rdd4/mft-data/genomes/final_experiments/sars-cov-2
PARSNP=/home/Users/ab235/parsnp_edits/parsnp_external_mums/parsnp

# New output directory
RESULTS=/dodo/ab235/actual-final/covid

THREADS=16

TESTS=(
  nucleotide
  mft_w11
  mft_w5
  mft_w8
  mft_w11_cov
  mft_w5_cov
  mft_w8_cov
)

mkdir -p "$RESULTS"

echo "Using base directory: $BASE"
echo "Using Parsnp: $PARSNP"
echo "Using results directory: $RESULTS"
echo "Using threads: $THREADS"
echo "ANI filtering: skipped with --skip-ani-filter"
echo

if [[ ! -x "$PARSNP" ]]; then
  echo "ERROR: Parsnp executable not found or not executable: $PARSNP"
  exit 1
fi

if [[ ! -d "$BASE" ]]; then
  echo "ERROR: Base directory not found: $BASE"
  exit 1
fi

for dataset_path in "$BASE"/n_*
do
  if [[ ! -d "$dataset_path" ]]; then
    continue
  fi

  dataset=$(basename "$dataset_path")

  echo "============================================================"
  echo "DATASET: $dataset"
  echo "============================================================"

  GENOME_DIR="$dataset_path/nucleotide"

  if [[ ! -d "$GENOME_DIR" ]]; then
    echo "Skipping $dataset: missing nucleotide genome directory: $GENOME_DIR"
    echo
    continue
  fi

  REF=$(find -L "$GENOME_DIR" -maxdepth 1 -type f \( -name "*.fna" -o -name "*.fasta" -o -name "*.fa" \) | sort | head -n 1)

  if [[ -z "${REF:-}" ]]; then
    echo "Skipping $dataset: no valid genome files found in $GENOME_DIR"
    echo
    continue
  fi

  echo "Reference genome: $REF"
  echo

  for test in "${TESTS[@]}"
  do
    MUMS="$dataset_path/${test}.mums"
    LENGTHS="$dataset_path/${test}.lengths"

    OUTDIR="$RESULTS/$dataset/$test"
    RUNLOG="$RESULTS/$dataset/${test}_run.log"
    TIMELOG="$RESULTS/$dataset/${test}_time.log"
    STATUSLOG="$RESULTS/$dataset/${test}_status.txt"

    mkdir -p "$RESULTS/$dataset"

    # Skip runs that already finished successfully.
    if [[ -f "$STATUSLOG" ]] && grep -q "^exit_code: 0$" "$STATUSLOG"; then
      echo "Skipping $dataset $test: already completed successfully"
      echo
      continue
    fi

    echo "------------------------------------------------------------"
    echo "Running dataset=$dataset test=$test"
    echo "------------------------------------------------------------"

    if [[ ! -f "$MUMS" ]]; then
      echo "Skipping $dataset $test: missing MUM file: $MUMS" | tee "$STATUSLOG"
      echo
      continue
    fi

    if [[ ! -f "$LENGTHS" ]]; then
      echo "Skipping $dataset $test: missing lengths file: $LENGTHS" | tee "$STATUSLOG"
      echo
      continue
    fi

    START_TIME=$(date)

    /usr/bin/time -v -o "$TIMELOG" "$PARSNP" \
      -r "$REF" \
      -d "$GENOME_DIR" \
      -o "$OUTDIR" \
      -p "$THREADS" \
      --external-mums "$MUMS" \
      --fo \
      --no-partition \
      --skip-ani-filter \
      --min-anchor-length 20 \
      --mum-length 10000000 \
      --skip-phylogeny \
      2>&1 | tee "$RUNLOG"

    EXIT_CODE=${PIPESTATUS[0]}
    END_TIME=$(date)

    {
      echo "dataset: $dataset"
      echo "test: $test"
      echo "reference: $REF"
      echo "genome_dir: $GENOME_DIR"
      echo "mums: $MUMS"
      echo "lengths: $LENGTHS"
      echo "output_dir: $OUTDIR"
      echo "start_time: $START_TIME"
      echo "end_time: $END_TIME"
      echo "exit_code: $EXIT_CODE"
    } > "$STATUSLOG"

    if [[ "$EXIT_CODE" -eq 0 ]]; then
      echo "Finished $dataset $test successfully"
    else
      echo "FAILED $dataset $test with exit code $EXIT_CODE"
      echo "Continuing to next run..."
    fi

    echo
  done
done

echo "============================================================"
echo "All ebola Parsnp runs finished"
echo "============================================================"
echo

SUMMARY="$RESULTS/summary_no_ani_filter.txt"

echo "Writing summary to: $SUMMARY"
echo

{
  echo "ebola Parsnp external-MUM summary"
  echo "ANI filtering skipped with --skip-ani-filter"
  echo "Generated: $(date)"
  echo

  for dataset_path in "$BASE"/n_*
  do
    if [[ ! -d "$dataset_path" ]]; then
      continue
    fi

    dataset=$(basename "$dataset_path")

    for test in "${TESTS[@]}"
    do
      OUTDIR="$RESULTS/$dataset/$test"
      LOG="$OUTDIR/log/parsnpAligner.log"
      TIMELOG="$RESULTS/$dataset/${test}_time.log"
      STATUSLOG="$RESULTS/$dataset/${test}_status.txt"
      REJECT="$OUTDIR/log/extmum_rejected.tsv"
      RUNLOG="$RESULTS/$dataset/${test}_run.log"

      echo "============================================================"
      echo "$dataset / $test"
      echo "============================================================"

      if [[ -f "$STATUSLOG" ]]; then
        cat "$STATUSLOG"
      else
        echo "No status log found"
      fi

      echo

      if [[ -f "$RUNLOG" ]]; then
        echo "Run warnings/errors:"
        grep -E "WARNING|CRITICAL|ERROR|from .lengths not found|too divergent|less than 1%|less than 10%|Parsnp finished|Aligned" "$RUNLOG" || true
      else
        echo "No run log found: $RUNLOG"
      fi

      echo

      if [[ -f "$LOG" ]]; then
        echo "Parsnp alignment summary:"
        grep -E "Number of MUM anchors found|Number of MUMs found:|Total MUMs found|Number of MUMs filtered|Number of Clusters filtered|Number of clusters created|Average number of MUMs per cluster|Average cluster length|Total coverage among all sequences" "$LOG" || true
      else
        echo "No Parsnp log found: $LOG"
      fi

      echo

      if [[ -f "$TIMELOG" ]]; then
        echo "Timing:"
        grep -E "Elapsed \(wall clock\) time|Maximum resident set size|User time|System time|Percent of CPU" "$TIMELOG" || true
      else
        echo "No timing log found: $TIMELOG"
      fi

      echo

      if [[ -f "$REJECT" ]]; then
        echo "Rejection reasons:"
        cut -f3 "$REJECT" | sort | uniq -c
      else
        echo "No rejection file found: $REJECT"
      fi

      echo
    done
  done
} > "$SUMMARY"

cat "$SUMMARY"

echo
echo "Done."

