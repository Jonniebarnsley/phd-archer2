#!/bin/bash/

module purge
module load user
module load bisicles/gia
module load python3 netcdf hdf5

module switch intel gnu         # switch compiler
module switch openmpi mvapich2  # switch mpi

module load anaconda
source activate bisicles

NCTOAMR=$BISICLES_HOME/BISICLES/BISICLES/code/filetools/nctoamr2d.Linux.*
PYTHON=/home/home01/earjbar/.conda/envs/bisicles/bin/python

if [ ! -f "smb.hdf5" ] ; then
    $PYTHON init_smb.@ID.py
    $NCTOAMR smb.nc smb.hdf5 smb
fi

conda deactivate
qsub job.@ID.sh
