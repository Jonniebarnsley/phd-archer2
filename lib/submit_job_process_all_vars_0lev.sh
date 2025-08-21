#!/bin/bash
# Usage: ./submit_job.sh VAR PLOTDIR NCDIR

# Argument check
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <plot_directory> <output_directory>"
    exit 1
fi

PLOTDIR=$1
NCDIR=$2
NAME=$(basename "$PWD")

export WORK=/mnt/lustre/a2fs-work2/work/n02/shared/jonnieb

mkdir -p output error

# Path to the original template script
TEMPLATE_SCRIPT="$WORK/templates/job.process_all_vars_0lev.sh"
JOB_SCRIPT="job.process_all_vars_0lev.sh"

# Copy and replace placeholders
sed \
  -e "s/@NAME/${NAME}/g" \
  -e "s|@PLOTDIR|${PLOTDIR}|g" \
  -e "s|@NCDIR|${NCDIR}|g" \
  "$TEMPLATE_SCRIPT" > "$JOB_SCRIPT"

# Make sure it's executable (optional)
chmod +x "$JOB_SCRIPT"

# Submit the job
sbatch "$JOB_SCRIPT"
