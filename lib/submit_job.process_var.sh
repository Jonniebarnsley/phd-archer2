#!/bin/bash

# Wrapper script for job.process_var.sh that customizes job name and output paths

if [ $# -ne 4 ]; then
	echo "usage: $0 <variable> <plot_directory> <nc_directory> <lev>"
	exit 1
fi

VAR=$1
PLOTDIR=$2
NCDIR=$3
LEV=$4

# Get the current directory name for job naming
NAME=$(basename $PWD)
JOB_NAME="${NAME}_${VAR}_${LEV}lev"

# Get the directory where this script is located
LIB=/work/n02/shared/jonnieb/lib/

# Submit the job with custom name and output paths
sbatch --job-name="$JOB_NAME" \
       --output="output/o.${JOB_NAME}.%j" \
       --error="error/e.${JOB_NAME}.%j" \
       "$LIB/job.process_var.sh" "$VAR" "$PLOTDIR" "$NCDIR" "$LEV"