#!/bin/env python

"""
Script to extract data from hdf5 plotfiles and save it as a netcdf.

Usage: "python process_plot.py <plot_directory> <outfile_path> <variable> [<variable> ...] [options]
Options:
 --lev   : level of refinement
 --order : interpolation order (0=piecewise constant, 1=linear)
"""

import argparse
import numpy as np
import xarray as xr
from pathlib import Path
from mpi4py import MPI # needed to run the MPI routines in amrio on archer2
from dask.diagnostics import ProgressBar

# NB: amrfile and, by extension, BisiclesFile need the BISICLES AMRfile directory added to PYTHONPATH 
# and the libamrfile directory added to LD_LIBRARY_PATH – see my .bashrc for an example
from bisiclesfile import BisiclesFile

class Processor:
    """
    Processor class to extract data from BISICLES plot files into a netcdf format. Uses amrfile python
    package via the BisiclesFile class to read all hdf5 files in a given plot directory and extract
    specified variables at a given level of refinement. Returns a single xarray Dataset concatenated
    along the time dimension and saves to a given filepath.
    
    :variables: List of variable names to extract, e.g. ['thickness', 'Z_base']
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

    @property
    def encoding_specs(self):
        """Encoding specifications for netcdf output"""
        xchunks = ychunks = 192 if self.lev == 0 else 768
        tchunks = 147 if self.lev == 0 else 49  # 2 time chunks for 0lev when simulating 2007-2300
        self.specs = {
            'zlib': True,
            'complevel': 4,
            'dtype': 'int32',
            'scale_factor': 0.001,   # 3 decimal places precision
            '_FillValue': -9999,
            'chunksizes': (tchunks, ychunks, xchunks)  # (time, y, x)
        }
        return self.specs

    def batch_time(self, files: list[Path]):
        """Concatenate all files along the time dimension"""

        times = []
        slices = []
        for i, file in enumerate(files, 1):
            print(f"({i}/{len(files)}) {file.name}")

            with BisiclesFile(file) as bfile:
                ds = bfile.read_dataset(self.variables, lev=self.lev, order=self.order)
                time = bfile.query_time()

            # Sometimes, multiple plotfiles can be written with times e.g. 200.0000 and 200.0001.
            # We skip files with times that are very close to the last time.
            if times and np.isclose(times[-1], time, atol=0.05):
                print(f"A time close to {time} already exists in dataset. Skipping file {file.name}.")
                continue

            times.append(time)
            slices.append(ds)
            
        batched = xr.concat(slices, dim='time')
        batched = batched.assign_coords(time=times)
        return batched

    def process_plot(self, plot_dir: Path, outfile: Path) -> None:
        """Extract data from a plot directory into a netcdf file"""

        if outfile.is_file():
            print(f'{outfile} already exists.')
            return
        
        files = sorted(plot_dir.glob('plot.*.2d.hdf5'))
        if len(files) == 0:
            print(f"No plot files found in {plot_dir}")
            return
        
        print(f"Processing variables: {', '.join(self.variables)} at level {self.lev} from {plot_dir}")
        ds = self.batch_time(files)
        for var in ds.data_vars:
            ds[var].encoding.update(self.encoding_specs)

        print("Chunking dataset for dask...")
        tc, yx, xc = self.encoding_specs['chunksizes']
        ds = ds.chunk({'time': tc, 'y': yx, 'x': xc})
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

def create_parser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(
        description="Process BISICLES plot files into a netcdf format")

    # add arguments
    parser.add_argument("plot_dir", type=Path, help="Path to BISICLES plot directory")
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
    proc.process_plot(args.plot_dir, args.outfile)

if __name__ == "__main__":
    main()
