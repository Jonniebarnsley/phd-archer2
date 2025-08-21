#!/bin/bash

# Argument check
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <variable> <plot_directory> <output_directory>"
    exit 1
fi

VAR=$1
PLOTDIR=$2
NCDIR=$3
NAME=$(basename "$PWD")

export WORK=/mnt/lustre/a2fs-work2/work/n02/shared/jonnieb

mkdir -p output error

# Path to the original template script
TEMPLATE_SCRIPT="$WORK/templates/job.process_var_3lev.sh"
JOB_SCRIPT="job.process_${VAR}_3lev.sh"

# Copy and replace placeholders
sed \
  -e "s/@NAME/${NAME}/g" \
  -e "s/@VAR/${VAR}/g" \
  -e "s|@PLOTDIR|${PLOTDIR}|g" \
  -e "s|@NCDIR|${NCDIR}|g" \
  "$TEMPLATE_SCRIPT" > "$JOB_SCRIPT"

# Make sure it's executable (optional)
chmod +x "$JOB_SCRIPT"

# Submit the job
sbatch "$JOB_SCRIPT"
