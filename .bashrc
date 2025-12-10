module load PrgEnv-gnu
module load cray-python
module load cdo
module load cray-hdf5-parallel
module load cray-netcdf-hdf5parallel
module load nco
module load cray-fftw

# bisicles and petsc directories
export WORK=/work/n02/shared/${USER}
export SCRATCH=/mnt/lustre/a2fs-nvme/work/n02/shared/jonnieb
export BISICLES_HOME=$WORK/bisicles
export PETSC_DIR=$BISICLES_HOME/petsc

# python paths
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/cray/pe/python/3.9.13.1/lib
export PYTHONPATH=$PYTHONPATH:/work/y07/shared/umshared/lib/python3.9

# bisicles amrfile python module
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$BISICLES_HOME/master/code/libamrfile
export PYTHONPATH=$PYTHONPATH:$BISICLES_HOME/master/code/libamrfile/python/AMRFile

# my library
export PYTHONPATH=$PYTHONPATH:$WORK/lib

# jupter paths
export JUPYTER_RUNTIME_DIR=$WORK/.local/share/jupyter/runtime
export PYTHONUSERBASE=$WORK/.local
export PATH=$PYTHONUSERBASE/bin:$PATH

# fftw path
export FFTWDIR=/opt/cray/pe/fftw/default/x86_64

# filetools
export NCTOAMR=$BISICLES_HOME/master/code/filetools/nctoamr2d.Linux.64.CC.ftn.OPT.MPI.PETSC.GNU.ex
export FLATTEN=$BISICLES_HOME/master/code/filetools/flatten2d.Linux.64.CC.ftn.OPT.MPI.PETSC.GNU.ex
export EXTRACT=$BISICLES_HOME/master/code/filetools/extract2d.Linux.64.CC.ftn.OPT.MPI.PETSC.GNU.ex

# aliases
alias q='squeue --format="%.10i %.10P %.20j %.8u %.8T %.10M %.12l %.6D %R" --me'
alias short='srun --nodes=1 --exclusive --time=00:20:00 --account=n02-LDNDTP1 --partition=standard --qos=short --reservation=shortqos --pty /bin/bash'
alias interactive='salloc --nodes=1 --ntasks-per-node=128 --cpus-per-task=1 --time=00:20:00 --partition=standard --qos=short --account=n02-LDNDTP1'
alias jlab='export JUPYTER_RUNTIME_DIR=$(pwd); jupyter lab --ip=0.0.0.0 --no-browser'
alias ls='ls --color=auto'

# expand bash variables
shopt -s direxpand


