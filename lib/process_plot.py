#!/bin/env python

"""
Script to extract data from hdf5 plotfiles and save it as a netcdf.

Usage: "python process_plot.py <variable> <plot_directory> [options]
Options:
 -d     : output_directory
 -f     : output_file
 --lev  : level of refinement

Use with either -d or -f, not both. If -d, the output will be sorted into automatically generated
subdirectories for level of refinement and variable. -f allows users to specify a custom filepath,
overriding anything defined by -d.
"""

import argparse
import xarray as xr
from pathlib import Path
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
    def encoding_specs(self):
        """Encoding specifications for netcdf output"""
        xchunks = ychunks = 192 if self.lev == 0 else 768
        tchunks = 147 if self.lev == 0 else 49  # 2 time chunks for 0lev when simulating 2007-2300
        self.specs = {
            'zlib': True,
            'complevel': 3,
            'dtype': 'int32',
            'scale_factor': 0.001,   # 3 decimal places precision
            '_FillValue': -9999,
            'chunksizes': (tchunks, ychunks, xchunks)  # (time, y, x)
        }
        return self.specs

    def batch_time(self, files: list[Path]):
        """Concatenate all files along the time dimension"""

        batched = None
        for i, file in enumerate(files, 1):
            print(f"({i}/{len(files)}) {file.name}")

            with BisiclesFile(file) as bfile:
                ds = bfile.read_dataset(self.variable, lev=self.lev)
                time = bfile.query_time()
            ds = ds.expand_dims('time')
            ds = ds.assign_coords(time=[time])

            if batched is None:
                batched = ds
            else:
                batched = xr.concat([batched, ds], dim='time')
            del ds

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
        
        print(f"Processing {self.variable} at level {self.lev} from {plot_dir}")
        ds = self.batch_time(files)
        ds[self.variable].encoding.update(self.encoding_specs)

        print(f"Generating {outfile}...")
        try:
            ds.to_netcdf(outfile)
            print(f"Successfully created {outfile}")
        except Exception as e:
            print(f"Error generating {outfile}: {e}")
            outfile.unlink()
        except KeyboardInterrupt:
            outfile.unlink()

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
        description="Process BISICLES plot files into a netcdf format")

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