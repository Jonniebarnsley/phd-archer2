#!/bin/bash
# Slurm job options (job-name, compute nodes, job time)
#SBATCH --job-name=@MODEL_@SCENARIO
#SBATCH --output=output/%A.%a.o
#SBATCH --error=error/%A.%a.e
#SBATCH --time=02:00:00
#SBATCH --nodes=1
#SBATCH --hint=nomultithread
#SBATCH --distribution=block:block
#SBATCH --account=n02-NES007229
#SBATCH --partition=standard
#SBATCH --qos=taskfarm
#SBATCH --array=1995-2014

export OMP_NUM_THREADS=1 # Set number of threads to 1
export HDF5_USE_FILE_LOCKING=FALSE

export RUNDIR=/mnt/lustre/a2fs-nvme/work/n02/n02/jonnieb/ocean_forcing
cd $RUNDIR

# check config file exists
CONFIG=@model/$SLURM_ARRAY_TASK_ID/config.@model
if [[ ! -f $CONFIG ]]; then
	echo "Config file $CONFIG not found"
	exit 1
fi

# delay to avoid too many jobs accessing the mapping file at once
DELAY=$(( (($SLURM_ARRAY_TASK_ID - $SLURM_ARRAY_TASK_MIN) % 32) * 20))
echo "Waiting for $DELAY seconds..."
sleep $DELAY

# run ocean forcing
singularity exec --bind $RUNDIR ocean_forcing.sif \
	python -m ismip6_ocean_forcing $CONFIG
