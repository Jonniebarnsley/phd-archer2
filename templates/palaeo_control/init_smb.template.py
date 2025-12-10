# script for calculating the initial smb using RACMO and pyPDD

import numpy as np
import xarray as xr
from pypdd import PDDModel

# read in forcing data
NCs = [
    '@TEMP',
    '@PRECIP'
]
vars = ['T2m', 'precip']

data = {}
for var, nc in zip(vars, NCs):
    ds = xr.open_dataset(nc)
    array = np.asarray(ds[var])
    nonan = np.nan_to_num(array)
    data[var] = nonan

temp = data['T2m'] - 273.15         # Kelvin to Celsius
precip = data['precip'] / 1000 * 12 # kgm^-2yr^-1 to myr^-1

# run PDD model
pdds = 0.004 # pdd factor snow
pddi = @PDDi # pdd factor ice
pdd = PDDModel(pdd_factor_snow = pdds, pdd_factor_ice = pddi)
pdd_results = pdd(temp, precip)
smb = pdd_results['smb']
 
ds = xr.Dataset({'smb': (('x', 'y'), smb)},
                coords={'x': np.arange(4.0e+3,6144.0e+3,8.0e+3) - 6144.0e+3*0.5,
                        'y': np.arange(4.0e+3,6144.0e+3,8.0e+3) - 6144.0e+3*0.5})
ds.to_netcdf('smb.nc', 'w')