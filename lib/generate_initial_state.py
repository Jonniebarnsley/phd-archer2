import sys
import argparse
import numpy as np
from mpi4py import MPI
from xarray import Dataset, DataArray

# NB: amrfile and, by extension, BisiclesFile need the BISICLES AMRfile directory added to PYTHONPATH 
# and the libamrfile directory added to LD_LIBRARY_PATH – see my .bashrc for an example
from bisiclesfile import BisiclesFile

def convert_C(C: DataArray, xVel: DataArray, yVel: DataArray, m: float=1.0, uf: float=None) -> DataArray:

    """
    Inverse problem is solved using a simple linear sliding law

    tau = C * u

    We would like to convert the inverted field for Weertman coefficient C into an 
    equivalent field for any sliding law such that drag is unchanged upon 
    initialisation.

    For a power law sliding law, this can be done by solving the equation that 
    equates both friction regimes.

    C * u = C_m * |u|^(m-1) * u     
    C_m = C * |u|^(1-m)

    In order to avoid areas of no slip where u = 0 causing C_m -> 0, we set a
    minimum sliding speed of 1 m·a⁻¹ when calculating the conversion factor.
    
    An optional parameter uf (fast sliding speed) may also be set so that C_m is
    converted into the field C_f for a regularised Coulomb sliding law like that of 
    Joughin et al (2019):

    tau = C_f * [uf*|u| / (|u|+uf)]^m * (u / |u|)

    N.B. this form differs from slightly from that of Joughin et al (2019), which
    is written:

    tau = C_j * [|u| / (|u|+uf)]^(1/m) * (u / |u|)

    However, these are equivalent with m = 1/m (different convention for exponent)
    and C_f = C_j / uf^m. BISICLES chooses this form so that the units for C_f
    match that of C in the original sliding law.

    Again, equating basal drag with that of our power law yields the conversion 
    formula:

    C_f = C_m * [|u|/uf + 1]^m
    """

    print(f'Converting C into equivalent field for m={m}...')
    u = np.hypot(xVel, yVel)
    u = u.where(u>1, 1) # avoid C_m -> 0 when u -> 0

    C_m = C * u **(1.0-m)
    
    if uf is None:
        return C_m
    else:
        print(f'Applying additional factor for fast sliding speed uf={uf} ma-1...')
        C_f = C_m * (u/uf + 1)**m
        return C_f

def generate_initial_state(infile: str, m: float=1.0, uf: float=None) -> Dataset:

    required_vars = ['thickness', 'Z_base', 'Cwshelf', 'muCoef', 'xVelb', 'yVelb']
    with BisiclesFile(infile) as bfile:
        ds = bfile.read_dataset(required_vars, lev=3)
    
    if m!=1.0 or uf is not None:
        ds['C_m'] = convert_C(ds.Cwshelf, ds.xVelb, ds.yVelb, m=m, uf=uf)
    else:
        ds['C_m'] = ds['Cwshelf']
    
    ds['C_m'].attrs['long_name'] = f'Weertman coefficient (m={m}, uf={uf})'
    ds['C_m'].attrs['units'] = 'Pa·m⁻¹·s'
    return ds

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Process inputs and options")

    # add arguments
    parser.add_argument("infile", type=str, help="path to ctrl.*.hdf5 file")
    parser.add_argument("outfile", type=str, help="path to output netcdf")

    # add optional arguments
    parser.add_argument("-m", type=float, default=1.0, help="value of Weertman exponent")
    parser.add_argument("-u", "--uf", type=float, help="fast sliding speed for regularised Coulomb sliding")
    parser.add_argument("--lev", type=int, default=3, help="max level of refinement")
    return parser

def main() -> None:

    parser = build_parser()
    args = parser.parse_args()
    try:
        ds = generate_initial_state(args.infile, m = args.m, uf = args.uf)
    except KeyboardInterrupt:
        print("Interrupted by user")
        return
    
    print(f'saving to {args.outfile}...')
    encoding = {
        var: {
            'zlib': True,          # enables compression
            'complevel': 4,        # compression level (1–9)
            'dtype': 'float32',    # reduce file size if precision allows
            '_FillValue': None     # avoids auto-inserting NaNs as fill values
        }
        for var in ds.data_vars
    }
    ds.to_netcdf(args.outfile, encoding=encoding)
    print('done')

if __name__ == "__main__":
    main()