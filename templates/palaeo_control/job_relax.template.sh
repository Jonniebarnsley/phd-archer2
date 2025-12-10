#!/bin/bash

#$ -cwd -V
#$ -l h_rt=02:00:00
#$ -l nodes=1
#$ -N "@JOBID"
#$ -m be
#$ -M earjbar@leeds.ac.uk
#$ -j y

date # start time

# prepare modules:
module purge
module load user
module load bisicles/gia
module load python3 netcdf hdf5

module switch intel gnu # switch compilers
module switch openmpi mvapich2 # switch mpi

module list

# environment variables
BASEDIR=$SGE_O_WORKDIR
PYDIR=$BASEDIR
export PYTHONPATH=$PYDIR
MV2_ENABLE_AFFINITY=0

# make plotfile directory if it doesn't exist
mkdir -p plotfiles_relax

# run bisicles:
mpirun driver2d inputs_relax.@ID

# tidy up
rm pout.*
mkdir -p checkpoints
mv chk.*.hdf5 checkpoints

source wrapper.@ID.sh
# end time:
date
