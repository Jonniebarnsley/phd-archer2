#!/bin/env python

"""
Script to extract data from hdf5 ctrl files and save it as a netcdf.

Usage: "python process_ctrl.py <ctrl_directory> <outfile_path> <variable> [<variable>...]

Options:
 --lev      : level of refinement
 --order    : interpolation method (0=piecewise constant, 1=linear)
"""

import re
import argparse
import xarray as xr
from pathlib import Path
from xarray import Dataset
from collections import defaultdict
from dask.diagnostics import ProgressBar
from mpi4py import MPI # needed to run the MPI routines in amrio on archer2

# NB: amrfile and, by extension, BisiclesFile need the BISICLES AMRfile directory added to PYTHONPATH 
# and the libamrfile directory added to LD_LIBRARY_PATH – see my .bashrc for an example
from bisiclesfile import BisiclesFile

class Processor:
    """
    Similar to process_plot.py but for ctrl files, which have an additional dimension
    (time, iteration, y, x) compared to plot files (time, y, x). First we organise files
    by time, then batch along the iteration dimension for each time, and finally batch
    along the time dimension to create a final dataset.
    
    :variables: List of variable names to extract, e.g. ['Cwshelf', 'muCoef']
    :lev: Level of refinement to extract (default=0)
    :order: Interpolation order (0=piecewise constant, 1=linear), default=0
    """

    def __init__(
        self, 
        variables: list, 
        lev: int=0,
        order: int=0
    ):
        self.variables = variables
        self.lev = lev
        self.order = order

    def encoding_specs(self, variable: str):
        """Encoding specifications for netcdf storage"""
        dtype = 'int16' if variable == 'muCoef' else 'int32'
        specs = {
            'zlib': True,
            'complevel': 3,
            'dtype': dtype,
            'scale_factor': 0.001,   # 3 decimal places precision
            '_FillValue': -9999,
            'chunksizes': (1, 16, 768, 768)  # (time, iteration, y, x)
        }
        return specs

    def batch_iterations(self, iter_file_pairs: list[tuple[int, Path]]) -> Dataset:
        """Concatenate all iterations in an inverse problem along the iteration dimension"""

        iter_slices = []
        for i, file in iter_file_pairs:
            print(f'  Processing iteration {i}: {file.name}')
            with BisiclesFile(file) as bfile:
                ds = bfile.read_dataset(self.variables, lev=self.lev, order=self.order)
            iter_slices.append(ds)
        
        iter_nums = [i for i, _ in iter_file_pairs]
        batched = xr.concat(iter_slices, dim='iteration')
        batched = batched.assign_coords(iteration=iter_nums)

        return batched
    
    def batch_time(self, files: list[Path]):
        """Concatenate all inverse problems along the time dimension"""

        iters = defaultdict(list)
        for file in files:
            time, iteration = get_time_and_iteration(file)
            iters[time].append((iteration, file))

        timeslices = []
        for time, tfiles in iters.items():
            print(f'Processing timestep {time} with {len(tfiles)} iterations')
            ds = self.batch_iterations(tfiles)
            timeslices.append(ds)

        batched = xr.concat(timeslices, dim='time')
        batched = batched.assign_coords(time=list(iters.keys()))
        return batched

    def process_ctrl(self, ctrl_dir: Path, outfile: Path) -> None:
        """Extract data from a ctrl directory into a netcdf file"""

        if outfile.is_file():
            print(f'{outfile} already exists.')
            return
        
        files = sorted(ctrl_dir.glob('ctrl.*.2d.hdf5'))
        if len(files) == 0:
            print(f"No ctrl files found in {ctrl_dir}")
            return
        
        print(f"Processing variables {', '.join(self.variables)} at level {self.lev} from {ctrl_dir}")
        ds = self.batch_time(files)
        for var in ds.data_vars:
            ds[var].encoding.update(self.encoding_specs(var))
        
        print("Preparing data to write...")
        ds = ds.chunk({'time': 1, 'iteration': 16, 'y': 768, 'x': 768})
        print(f"Generating {outfile}...")
        try:
            with ProgressBar():
                ds.to_netcdf(outfile)
            print(f"Successfully created {outfile}")
        except Exception as e:
            print(f"Error generating {outfile}: {e}")
            outfile.unlink()
        except KeyboardInterrupt:
            outfile.unlink()
        print('done')

def get_time_and_iteration(file: Path):

    """
    Extract two 6-digit numbers from a filename like:
    'ctrl.lasagne.run001.03lev.000015000013.2d.hdf5'
    
    Returns (first_number, second_number) as ints, eg: 000015 and
    000013 -> (15, 13)

    Exact conversion of time value will depend on the BISICLES option
    dt_typical found in the inputs script.
    """
    pattern = re.compile(r"\.(\d{6})(\d{6})\.")
    match = pattern.search(file.name)
    if not match:
        raise ValueError(f"No 6+6 digit block found in {file}")
    dt_typical = 1 # see BISICLES inputs
    time = float(match.group(1)) * dt_typical
    iteration = int(match.group(2))
    
    return time, iteration

def create_parser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(
        description="Process BISICLES ctrl files into a netcdf format")
    
    # add arguments
    parser.add_argument("ctrl_dir", type=Path, help="Path to BISICLES output directory")
    parser.add_argument("outfile", type=Path, help="Filepath for output netcdf file")
    parser.add_argument("variables", type=str, nargs='+', help="One or more variable names") 

    # add optional arguments
    parser.add_argument("--lev", type=int, default=0, help="level of refinement")
    parser.add_argument("--order", type=int, default=0, help="interpolation order (0=piecewise constant, 1=linear)")

    return parser

def main():

    parser = create_parser()
    args = parser.parse_args()
    args.outfile.parent.mkdir(parents=True, exist_ok=True)
    proc = Processor(variables=args.variables, lev=args.lev)
    proc.process_ctrl(args.ctrl_dir, args.outfile)

if __name__ == "__main__":
    main()