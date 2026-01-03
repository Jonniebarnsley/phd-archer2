#!/bin/bash
#SBATCH --job-name=combine_@MODEL_@SCENARIO
#SBATCH --output=output/%A.%a.o
#SBATCH --error=error/%A.%a.e
#SBATCH --time=01:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --hint=nomultithread
#SBATCH --distribution=block:block
#SBATCH --account=n02-NES007229
#SBATCH --partition=standard
#SBATCH --qos=taskfarm
#SBATCH --array=1-16

export OMP_NUM_THREADS=1
export HDF5_USE_FILE_LOCKING=FALSE

export RUNDIR=/mnt/lustre/a2fs-nvme/work/n02/n02/jonnieb/ocean_forcing
cd $RUNDIR

# Get the decade folder for this array task
DECADE=$(sed -n "${SLURM_ARRAY_TASK_ID}p" @model/decades.list)

CONFIG="@model/$DECADE/config.combine_@model"
if [[ ! -f $CONFIG ]]; then
    echo "Config file $CONFIG not found"
    exit 1
fi

# Run ocean forcing
singularity exec --bind $RUNDIR ocean_forcing.sif \
    python -m ismip6_ocean_forcing "$CONFIG"
