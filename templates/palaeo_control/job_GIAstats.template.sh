#!/bin/bash

#$ -cwd -V
#$ -l h_rt=48:00:00
#$ -pe smp 1
#$ -l h_vmem=2G
#$ -N "@JOBID_stats"
#$ -m be
#$ -j y
#$ -M earjbar@leeds.ac.uk

echo "start time: $(date)"

module purge
module load user
module load netcdf hdf5
module switch intel gnu

# load basin-finding functions from utils
#source $HOME/libs/utils.sh

# set mask
#MASK=$HOME/data/rignot_basins_16km.hdf5

# iterate over basins (1-27 for zwally, 0-18 for Rignot)
#for BASIN_ID in {00..18}; do
#    BASIN=$(getRignotbasin $BASIN_ID)
#    basin_stats="GIAstats/Rignot/${BASIN}" # directory for statsfiles
bash $HOME/libs/GIAstats.sh plotfiles GIAstats
#done

echo "finish time: $(date)"
