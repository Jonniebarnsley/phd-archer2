#!/bin/bash
# Slurm job options (job-name, compute nodes, job time)
#SBATCH --job-name=process_0lev
#SBATCH --output=output/process_0lev_%A_%a.o
#SBATCH --error=error/process_0lev_%A_%a.e
#SBATCH --time=00:20:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=6
#SBATCH --cpus-per-task=1
#SBATCH --hint=nomultithread
#SBATCH --distribution=block:block
#SBATCH --account=n02-NES007229
#SBATCH --partition=standard
#SBATCH --qos=short
#SBATCH --array=@START-@END

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

start=$(date +%s)
echo Start time is `date`

# get run directory from slurm array ID
RUN_ID=$(printf "%03d" $SLURM_ARRAY_TASK_ID)
RUN_DIR=run${RUN_ID}

# process netcdf
for var in thickness dThickness/dt xVel yVel Z_base Z_surface; do
	srun --nodes=1 --ntasks=1 --ntasks-per-node=1 --exact --mem=32G \
		python -u $WORK/lib/process_netcdf.py --lev 0 $var $RUN_DIR/plot @NCDIR &
done
wait

end=$(date +%s)
echo End time is `date`
echo Time elapsed: $(time_elapsed $start $end)