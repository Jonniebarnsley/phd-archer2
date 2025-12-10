import sys
import argparse
import numpy as np
from mpi4py import MPI
from xarray import Dataset, DataArray

# import amrfile – requires PYTHONPATH and LD_LIBRARY_PATH correctly set
from amrfile import io as amrio

def convert_C(C: DataArray, xVel: DataArray, yVel: DataArray, m: float=1.0, uf: float=None) -> DataArray:

    '''
    Inverse problem is solved using a simple linear sliding law, based on a power 
    relationship between velocity u and drag tau:

    tau = C|u|^(m-1) * u                                                (1)

    or equivalently      

    |tau| = C|u|^m                                                      (2)

    with exponent m = 1. We would like to convert the inverted field for Weertman 
    coefficient C into an equivalent field for any m such that drag is unchanged 
    upon initialisation.

    This can be done by solving the equation that equates both friction regimes.

    C|u| = C_m|u|^m                                                     (3)
    C_m = C|u|^(1-m)                                                    (4)

    However, this will result in C_m << 1 where |u| << 1. To avoid this, we instead
    convert using:

    C_m = C * [1+|u|^(1-m)]                                             (5)

    When |u| << 1, this ensures that C_m > C.
    When |u| >> 1, this approaches eq. (4)

    An optional parameter uf (fast sliding speed) may also be set so that C_m is
    converted into the field for a regularised Coulomb sliding law like that of 
    Joughin et al (2019):

    tau = C_f * [ uf*|u| / (|u|+uf) ]^m * (u / |u|)                     (6)

    N.B. this form differs from slightly from that of Joughin et al (2019), which
    is written:

    tau = C_j * [ |u| / (|u|+uf) ]^(1/m) * (u / |u|)                    (7)

    However, these are equivalent with m = 1/m (different convention for exponent)
    and C_f = C_j / uf^m. BISICLES chooses this form so that the units for C_f
    match that of C in the original sliding law.

    Again, equating basal drag with that of our power law yields the conversion 
    formula:

    C_f = C_m * [ |u|/uf + 1 ]^m                                        (8)
    '''

    print(f'Converting C into equivalent field for m={m}...')
    u = np.hypot(xVel, yVel)
    epsilon = 0 # small value to prevent zero bed friction
    C_m = C * (epsilon + u)**(1.0-m)
    
    if uf is None:
        return C_m
    else:
        print(f'Applying additional factor for fast sliding speed uf={uf} ma-1...')
        C_f = C_m * (u/uf + 1)**m
        return C_f

def extract_data(file: str, lev: int=3, order: int=0) -> Dataset:
   
    attrs = {
            'thickness' : {'long_name': 'Ice thickness', 'units': 'm'},
            'Z_base'    : {'long_name': 'Bed elevation', 'units': 'm'},
            'Cwshelf'   : {'long_name': 'Weertman friction coefficient (m=1)', 'units': 'Pa·m⁻¹·s'},
            'muCoef'    : {'long_name': 'Viscosity coefficient'},
            'xVelb'     : {'long_name': 'Basal x-velocity', 'units': 'm/a'},
            'yVelb'     : {'long_name': 'Basal y-velocity', 'units': 'm/a'}
            }
            
    # load hdf5 file
    amrID = amrio.load(file)
    lo, hi = amrio.queryDomainCorners(amrID, lev)
    
    # read data
    data = {}
    varnames = ['thickness', 'Z_base', 'Cwshelf', 'muCoef', 'xVelb', 'yVelb']
    for var in varnames:
        print(f'extracting {var}...')
        x0, y0, field = amrio.readBox2D(amrID, lev, lo, hi, var, order)
        data[var] = (['y', 'x'], field, attrs[var])
    
    # make dataset
    ds = Dataset(
            data,
            coords = {'x': x0, 'y': y0},
            )

    amrio.free(amrID)
    
    return ds

def main(args) -> None:

    infile = args.infile
    outfile = args.outfile
    lev = args.lev  # default 3
    m = args.m if args.m else 1
    uf = args.uf if args.uf else None

    ds = extract_data(infile, lev=lev)
    
    if m!=1 or uf is not None:
        ds['C_m'] = convert_C(ds.Cwshelf, ds.xVelb, ds.yVelb, m=m, uf=uf)
    else:
        ds['C_m'] = ds['Cwshelf']
    
    ds['C_m'].attrs['long_name'] = f'Weertman coefficient (m={m}, uf={uf})'
    ds['C_m'].attrs['units'] = 'Pa·m⁻¹·s'  # or appropriate
    
    print(f'saving to {outfile}...')
    encoding = {
        var: {
            'zlib': True,          # enables compression
            'complevel': 4,        # compression level (1–9)
            'dtype': 'float32',    # reduce file size if precision allows
            '_FillValue': None     # avoids auto-inserting NaNs as fill values
        }
        for var in ds.data_vars
    }
    ds.to_netcdf(outfile, encoding=encoding)
    print('done')


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Process inputs and options")

    # add arguments
    parser.add_argument("infile", type=str, help="path to ctrl.*.hdf5 file")
    parser.add_argument("outfile", type=str, help="path to output netcdf")

    # add optional arguments
    parser.add_argument("-m", type=float, help="value of Weertman exponent")
    parser.add_argument("--uf", type=float, help="fast sliding speed for regularised Coulomb sliding")
    parser.add_argument("--lev", type=int, default=3, help="max level of refinement")

    args = parser.parse_args()

    try:
        main(args)
    except KeyboardInterrupt:
        sys.exit('\nInterrupted by user')

