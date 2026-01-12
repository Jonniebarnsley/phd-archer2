#!/bin/bash
# Slurm job options (job-name, compute nodes, job time)
#SBATCH --job-name=process_0lev
#SBATCH --output=output/process_0lev_%A_%a.o
#SBATCH --error=error/process_0lev_%A_%a.e
#SBATCH --time=01:00:00
#SBATCH --nodes=1
#SBATCH --hint=nomultithread
#SBATCH --distribution=block:block
#SBATCH --account=n02-NES007229
#SBATCH --partition=standard
#SBATCH --qos=taskfarm
#SBATCH --array=16-16

export OMP_NUM_THREADS=1 # Set number of threads to 1
export SRUN_CPUS_PER_TASK=$SLURM_CPUS_PER_TASK # Propagate cpus-per-task from slurm to srun

# Export paths
export WORK=/mnt/lustre/a2fs-work2/work/n02/shared/jonnieb/
export BISICLES_BRANCH=$WORK/bisicles/master

# Load python, export paths for AMRfile, and activate python env for postprocessing
module load cray-python
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$BISICLES_BRANCH/code/libamrfile
export PYTHONPATH=$PYTHONPATH:$BISICLES_BRANCH/code/libamrfile/python/AMRFile
source $WORK/env/bin/activate

OUTDIR=ncs/0lev

# get run directory from slurm array ID
RUN_NUM=$(printf "%03d" $SLURM_ARRAY_TASK_ID)
PLOT=run${RUN_NUM}/plot

FILENAME="AIS_ssp585_p${RUN_NUM}_8km_2007-2300.nc"
FILEPATH=$OUTDIR/$FILENAME

python -u $WORK/lib/process_plot.py $PLOT $FILEPATH thickness Z_base Z_surface \
	xVel yVel activeSurfaceThicknessSource activeBasalThicknessSource
