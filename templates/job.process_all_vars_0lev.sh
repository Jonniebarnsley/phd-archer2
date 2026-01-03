#!/bin/bash
#SBATCH --job-name=process_@NAME
#SBATCH -o output/process_vars_0lev.%j.o
#SBATCH -e error/process_vars_0lev.%j.e
#SBATCH --partition=standard
#SBATCH --nodes=1
#SBATCH --time=00:20:00
#SBATCH --qos=short
#SBATCH --account=n02-NES007229
#SBATCH --hint=nomultithread
#SBATCH --distribution=block:block

# set paths
export WORK=/mnt/lustre/a2fs-work2/work/n02/shared/jonnieb/
export BISICLES=$WORK/bisicles/master

# load python
module load cray-python
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$BISICLES/code/libamrfile
export PYTHONPATH=$PYTHONPATH:$BISICLES/code/libamrfile/python/AMRFile
source $WORK/env/bin/activate

# load some helpful functions
source $WORK/lib/utils.sh

start=$(date +%s)
echo Start time is `date`

cd $SLURM_SUBMIT_DIR
python -u $WORK/lib/process_plot.py --lev 0 @PLOTDIR @NCDIR thickness dThickness/dt xVel yVel Z_base Z_surface 

end=$(date +%s)
echo End time is `date`
echo Time elapsed: $(time_elapsed $start $end)

