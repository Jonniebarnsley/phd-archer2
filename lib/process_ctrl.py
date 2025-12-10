#!/bin/env python

"""
Script to extract data from hdf5 ctrl files and save it as a netcdf.

Usage: "python process_ctrl.py <variable> <ctrl_directory> [options]
Options:
 -d     : output_directory
 -f     : output_file
 --lev  : level of refinement

Use with either -d or -f, not both. If -d, the output will be sorted into automatically generated
subdirectories for level of refinement and variable. -f allows users to specify a custom filepath,
overriding anything defined by -d.
"""

import re
import argparse
import xarray as xr
from pathlib import Path
from collections import defaultdict
from xarray import DataArray, Dataset
from mpi4py import MPI # needed to run the MPI routines in amrio on archer2

# NB: amrfile needs the BISICLES AMRfile directory added to PYTHONPATH and the libamrfile directory
# added to LD_LIBRARY_PATH – see my .bashrc for an example
from bisiclesio import BisiclesFile

class Processor:

    def __init__(
        self, 
        variable: str, 
        lev: int=0,
    ):
        self.variable = variable
        self.lev = lev

    @property
    def specs(self):
        """Encoding specifications for netcdf storage"""
        dtype = 'int16' if self.variable == 'muCoef' else 'int32'
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

        batched = None
        for iteration, file in iter_file_pairs:
            print(f'  Processing iteration {iteration}: {file.name}')
            with BisiclesFile(file) as bfile:
                ds = bfile.read_dataset(self.variable, lev=self.lev)
            ds = ds.expand_dims('iteration')
            ds = ds.assign_coords(iteration=[iteration])

            if batched is None:
                batched = ds
            else:
                batched = xr.concat([batched, ds], dim='iteration')
            del ds

        return batched
    
    def batch_timesteps(self, files: list[Path]):
        """Concatenate all inverse problems along the time dimension"""

        iters = defaultdict(list)
        for file in files:
            time, iteration = get_time_and_iteration(file)
            iters[time].append((iteration, file))

        batched = None
        for time, tfiles in iters.items():
            print(f'Processing timestep {time} with {len(tfiles)} iterations')
            ds = self.batch_iterations(tfiles)
            ds = ds.expand_dims('time')
            ds = ds.assign_coords(time=[time])
            if batched is None:
                batched = ds
            else:
                batched = xr.concat([batched, ds], dim='time')
            del ds

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
        
        print(f"Processing {self.variable} at level {self.lev} from {ctrl_dir}")
        ds = self.batch_timesteps(files)
        ds[self.variable].encoding.update(self.specs)

        print(f"Generating {outfile}...")
        try:
            ds.to_netcdf(outfile)
            print(f"Successfully created {outfile}")
        except Exception as e:
            print(f"Error generating {outfile}: {e}")
            outfile.unlink()
        except KeyboardInterrupt:
            outfile.unlink()

def get_time_and_iteration(file: Path):

    """
    Extract two 6-digit numbers from a filename like:
    'ctrl.lasagne.run001.03lev.000150000013.2d.hdf5'
    
    Returns (first_number, second_number) as ints, eg: 000150 and
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

def auto_filepath(ctrl_dir: Path, savedir: Path, variable: str, lev: int) -> Path:
    """
    Generates a filepath for the processed netcdf following the directory structure:
    <savedir>/<lev>lev/<variable>/<ensemble>_<run>_<variable>_<lev>lev.nc
    """

    ctrl_dir = ctrl_dir.resolve()
    run = ctrl_dir.parent
    ensemble = run.parent

    auto_dir = savedir / f'{lev}lev' / variable 
    auto_path = auto_dir / f'{ensemble.name}_{run.name}_{variable}_{lev}lev.nc'

    return auto_path

def create_parser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(
        description="Process BISICLES ctrl files into a netcdf format")
    
    # add arguments
    parser.add_argument("variable", type=str, help="variable name") 
    parser.add_argument("ctrl", type=Path, help="Path to BISICLES output directory")

    # add optional arguments
    parser.add_argument("--lev", type=int, default=0, help="level of refinement")
    parser.add_argument("-d", "--dir", type=Path, help="Directory to save netcdf files")
    parser.add_argument("-f", "--file", type=Path, help="Filepath for output netcdf file")

    return parser

def main():

    parser = create_parser()
    args = parser.parse_args()

    if args.file:
        outfile_path = args.file
        absolute_path = outfile_path.resolve()
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
    elif args.dir:
        outfile_path = auto_filepath(args.ctrl, args.dir, args.variable, args.lev)
        absolute_path = outfile_path.resolve()
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        print("Must either specify a directory (-d) or filepath (-f) for output")
        return

    proc = Processor(variable=args.variable, lev=args.lev)
    proc.process_ctrl(args.ctrl, outfile_path)

if __name__ == "__main__":
    main()
