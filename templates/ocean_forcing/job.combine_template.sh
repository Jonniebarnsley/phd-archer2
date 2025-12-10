#!/bin/bash
# Slurm job options (job-name, compute nodes, job time)
#SBATCH --job-name=@MODEL_@SCENARIO
#SBATCH --output=output/%j.o
#SBATCH --error=error/%j.e
#SBATCH --time=01:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --hint=nomultithread
#SBATCH --distribution=block:block
#SBATCH --account=n02-NES007229
#SBATCH --partition=standard
#SBATCH --qos=taskfarm

export OMP_NUM_THREADS=1 # Set number of threads to 1
export HDF5_USE_FILE_LOCKING=FALSE

# Get the year from the first command-line argument
YEARS=$1

# Check if YEAR was provided
if [[ -z "$YEARS" ]]; then
    echo "Error: No year provided. Usage: sbatch run_script.sh <year>"
    exit 1
fi

export RUNDIR=/mnt/lustre/a2fs-nvme/work/n02/n02/jonnieb/ocean_forcing
cd $RUNDIR

# check config file exists
CONFIG=@model/$YEARS/config.combine_@model
if [[ ! -f $CONFIG ]]; then
	echo "Config file $CONFIG not found"
	exit 1
fi

# run ocean forcing
echo "Running ismip6_ocean_forcing on $CONFIG"
singularity exec --bind $RUNDIR ocean_forcing.sif \
	python -m ismip6_ocean_forcing $CONFIG
