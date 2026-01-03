#!/bin/bash
# Slurm job options (job-name, compute nodes, job time)
#SBATCH --job-name=process_var_3lev
#SBATCH --output=output/process_var_3lev_%j.o
#SBATCH --error=error/process_var_3lev_%j.e
#SBATCH --time=00:20:00
#SBATCH --nodes=1
#SBATCH --hint=nomultithread
#SBATCH --distribution=block:block
#SBATCH --account=n02-NES007229
#SBATCH --partition=standard
#SBATCH --qos=short

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

# load some helpful functions
source $WORK/lib/utils.sh

VAR=$1
PLOT=$2
NC=$3

start=$(date +%s)
echo Start time is `date`

# process netcdf
python -u $WORK/lib/process_plot.py --lev 3 $PLOT $NC $VAR

end=$(date +%s)
echo End time is `date`
echo Time elapsed: $(time_elapsed $start $end)
