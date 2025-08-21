#!/bin/env python

'''
Script to extract data from hdf5 plotfiles and save it as a netcdf.

Usage: "python run_to_netcdf.py <run_directory> <variable>"
'''

import argparse
import numpy as np
import xarray as xr
from xarray import DataArray, Dataset
from pathlib import Path
import gc
from mpi4py import MPI # needed to run the MPI routines in amrio on archer2

# NB: amrfile needs the BISICLES AMRfile directory added to PYTHONPATH and the libamrfile directory
# added to LD_LIBRARY_PATH – see my .bashrc for an example
from amrfile import io as amrio


MAX_TIME = 2300     # cuts off data at any time above this value
FILL_VALUE = -9999  # fill NaNs in netcdf with this value
DEFAULT_LEV = 0  # default level of refinement
CHUNKS = {'x': 192, 'y': 192, 'time': 147}

# specs for encoding data.
specs = {
    'thickness'                      : {'conversion':1.0, 'prec':0.01, 'dtype':'int32', 'units':'m'},
    'Z_surface'                      : {'conversion':1.0, 'prec':0.01, 'dtype':'int32', 'units':'m'},
    'Z_base'                         : {'conversion':1.0, 'prec':0.01, 'dtype':'int32', 'units':'m'},
    'Z_bottom'                       : {'conversion':1.0, 'prec':0.01, 'dtype':'int32', 'units':'m'},
    'bTemp'                          : {'conversion':1.0, 'prec':0.01, 'dtype':'int32', 'units':'K'},
    'sTemp'                          : {'conversion':1.0, 'prec':0.01, 'dtype':'int32', 'units':'K'},
    'calvingFlux'                    : {'conversion':1.0, 'prec':0.01, 'dtype':'int32', 'units':''},
    'calvingRate'                    : {'conversion':1.0, 'prec':0.01, 'dtype':'int32', 'units':''},
    'dragCoef'                       : {'conversion':1.0, 'prec':0.01, 'dtype':'int32', 'units':''},
    'viscosityCoef'                  : {'conversion':1.0, 'prec':0.01, 'dtype':'int32', 'units':''},
    'iceFrac'                        : {'conversion':1.0, 'prec':0.01, 'dtype':'int32', 'units':''},
    'basal_friction'                 : {'conversion':1.0, 'prec':1.00, 'dtype':'int32', 'units':''},
    'surfaceThicknessSource'         : {'conversion':1000.0, 'prec':1.0, 'dtype':'int32', 'units':'mm/yr'},
    'activeSurfaceThicknessSource'   : {'conversion':1000.0, 'prec':1.0, 'dtype':'int32', 'units':'mm/yr'},
    'basalThicknessSource'           : {'conversion':1000.0, 'prec':1.0, 'dtype':'int32', 'units':'mm/yr'},
    'activeBasalThicknessSource'     : {'conversion':1000.0, 'prec':1.0, 'dtype':'int32', 'units':'mm/yr'},
    'tillWaterDepth'                 : {'conversion':1000.0, 'prec':1.0, 'dtype':'int32', 'units':'mm'},
    'waterDepth'                     : {'conversion':1000.0, 'prec':1.0, 'dtype':'int32', 'units':'mm'},
    'mask'                           : {'conversion':1.0, 'prec':1.00, 'dtype':'int16', 'units':''}, 
    'yVel'                           : {'conversion':1.0, 'prec':0.01, 'dtype':'int32', 'units':'m/yr'},
    'xVel'                           : {'conversion':1.0, 'prec':0.01, 'dtype':'int32', 'units':'m/yr'},
    'ybVel'                          : {'conversion':1.0, 'prec':0.01, 'dtype':'int32', 'units':'m/yr'},
    'xbVel'                          : {'conversion':1.0, 'prec':0.01, 'dtype':'int32', 'units':'m/yr'},
    'xVelb'                          : {'conversion':1.0, 'prec':0.01, 'dtype':'int32', 'units':'m/yr'},
    'yVelb'                          : {'conversion':1.0, 'prec':0.01, 'dtype':'int32', 'units':'m/yr'},
    'Cwshelf'                        : {'conversion':1.0, 'prec':0.01, 'dtype':'int32', 'units':''},
    'muCoef'                         : {'conversion':1.0, 'prec':0.01, 'dtype':'int32', 'units':''},
    'dThickness/dt'                  : {'conversion':1.0, 'prec':0.01, 'dtype':'int32', 'units':'m/yr'},
    }

def extract_field(variable: str, file: Path, lev: int=0, order: int=0) -> Dataset:

    '''
    Extracts time and variable data from a .hdf5 file and returns an xarray dataset

    :param variable: variable name
    :param file: path to a BISICLES output file (*.2d.hdf5)
    :param lev: level of refinement
    :param order: ??? just leave as 0

    :return time: time of file
    :return ds: xarray dataset of variable
    '''

    # read hdf5
    amrID = amrio.load(file)
    time = amrio.queryTime(amrID)
    lo, hi = amrio.queryDomainCorners(amrID, lev)
    x0, y0, field = amrio.readBox2D(amrID, lev, lo, hi, variable, order)
    
    # convert into correct units
    conversion_factor = specs[variable]['conversion']
    units = specs[variable]['units']
    field_in_units = np.asarray(field) * conversion_factor
    variable = variable.replace('/', '') # dThickness/dt causes problems – can't have '/' in var name

    # make Dataset
    ds = Dataset({
        variable: DataArray(
            data = field_in_units,
            dims = ['y', 'x'],
            coords = {'x': x0, 'y': y0},
            attrs = {'units': units}
        )})
    amrio.free(amrID)

    return time, ds

def generate_netcdf(variable: str, dir: Path, outnc: Path, lev: int=0, overwrite: bool=False) -> None:

    '''
    Generates a netcdf of the given variable from the output files of a BISICLES run.
    Memory-efficient version that builds the dataset incrementally.

    :param variable:    variable name
    :param dir:         path to output file directory
    :param outnc:       path for output netcdf
    :param lev:         level of refinement (0 by default, the most coarse resolution)
    :param overwrite:   will overwrite any existing netcdfs if True (False by default)
    '''

    # skip if file already exists
    if outnc.is_file() and not overwrite:
        print(f'{outnc} already exists.')
        return

    files = sorted(dir.glob('*.2d.hdf5'))
    total = len(files)
    if total == 0:
        print(f"No plotfiles found in {dir}")
        return

    print(f"Processing {total} files...")
    
    # Get encoding info
    precision = specs[variable]['prec']
    dtype = specs[variable]['dtype']
    variable_clean = variable.replace('/', '')
    
    # Process files and build dataset incrementally
    growing_ds = None
    processed_count = 0
    
    for i, file in enumerate(files, 1):
        print(f'Processing ({i}/{total}) {file.name}')
        
        # Extract data from current file
        time, current_ds = extract_field(variable, str(file), lev=lev)
        
        # Check if time is within range
        if time > MAX_TIME:
            print(f'  Skipping {file.name} (time {time} > {MAX_TIME})')
            del current_ds
            gc.collect()
            continue
        
        # Assign time coordinate to the dataset
        current_ds = current_ds.expand_dims('time')
        current_ds = current_ds.assign_coords(time=[time])
        
        # Initialize or append to the growing dataset
        if growing_ds is None:
            growing_ds = current_ds
            processed_count = 1
        else:
            growing_ds = xr.concat([growing_ds, current_ds], dim='time')
            processed_count += 1
        
        # Clear memory immediately
        del current_ds
        gc.collect()
    
    if growing_ds is None:
        print("No files found within time range.")
        return
    
    print(f"Successfully processed {processed_count} files within time range.")

    growing_ds = growing_ds.chunk(CHUNKS)

    # Apply final encoding
    growing_ds[variable_clean].encoding.update({
        'zlib': True,
        'complevel': 6,
        'dtype': dtype,
        'scale_factor': precision,
        '_FillValue': FILL_VALUE
    })
    
    # Save the final dataset
    print(f"Generating {outnc}...")
    growing_ds.to_netcdf(outnc)
    
    print(f"Successfully created {outnc}")

def get_outfile_path(variable: str, plotdir: Path, savedir: Path, lev: int) -> Path:

    '''
    Generates a name for an output netcdf in the format:

        <ensemble-name>_<run-name>_<variable>_<level-of-refinement>.nc

    NB This assumes that the directory structure for the ensemble is as follows:

        - ensemble home directory
            - run directory
                - plotfile directory (plotdir)
                    - plotfile 1
                    - plotfile 2
                    etc...

    :param variable:    variable name
    :param plotdir:     path to plotfile directory
    :param savedir:     path to a directory in which to save the netcdfs
    :param lev:         level of refinement (0 by default, the most coarse resolution)
    '''

    plotdir = plotdir.resolve()
    run = plotdir.parent
    ensemble = run.parent
    variable = variable.replace('/', '') # dThickness/dt causes problems with path

    varsavedir = savedir / f'{lev}lev' / variable 
    varsavedir.mkdir(parents=True, exist_ok=True)

    outpath = varsavedir / f'{ensemble.name}_{run.name}_{variable}_{lev}lev.nc'

    return outpath

def main(args) -> None:

    '''
    When called from the command line, this script takes three arguments:

        - The variable to process
        - The plotfile directory to work on
        - The save directory in which the netcdfs will be saved

    Additionally, the option --lev can be called with the level of refinement with
    which to generate the netcdfs.

    main() takes those arguments, generates a path for the output netcdf based on the
    ensemble directory structure [see get_outfile_path()], then processes and saves
    the netcdf using memory-efficient incremental processing.
    '''
    
    variable = args.variable
    directory = Path(args.directory)
    savedir = Path(args.savedir)
    lev = args.lev if args.lev else DEFAULT_LEV

    outfile_path = get_outfile_path(variable, directory, savedir, lev)
    generate_netcdf(variable, directory, outfile_path, lev=lev)


if __name__== '__main__':
    parser = argparse.ArgumentParser(
        description="Process inputs and options"
        )

    # add arguments
    parser.add_argument("variable", type=str, help="variable name") 
    parser.add_argument("directory", type=str, help="Path to BISICLES output directory")
    parser.add_argument("savedir", type=str, help="Path to save directory")

    # add optional arguments
    parser.add_argument("--lev", type=int, default=DEFAULT_LEV, help="level of refinement")

    args = parser.parse_args()
    print(f'running on args: {args.variable}, {args.directory}, {args.savedir}')
    main(args)
