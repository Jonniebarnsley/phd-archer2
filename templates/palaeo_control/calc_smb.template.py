# script for calculating smb using pypdd, including corrections for ice sheet elevation

import sys
import glob
import numpy as np
import xarray as xr
from pypdd import PDDModel
from skimage.measure import block_reduce

# import amrio
genpath = '/nobackup/earjo/python_modules'
sys.path.append(genpath)
from amrfile import io as amrio

# read in forcing data
NCs = [
    '@TEMP',
    '@PRECIP',
    '@HEIGHT'
]
vars = ['T2m', 'precip', 'height']

data = {}
for var, nc in zip(vars, NCs):
    ds = xr.open_dataset(nc)
    array = np.asarray(ds[var])
    nonan = np.nan_to_num(array)
    data[var] = nonan

temp = data['T2m'] - 273.15 # Kelvin to Celsius
precip = data['precip'] / 1000 * 12 # kgm^-2yr^-1 to myr^-1
height = data['height']

# read in plotfile
plotfiles = sorted(glob.glob('plotfiles/plot*.hdf5'))
latest_plotfile = plotfiles[-1]
amrID = amrio.load(latest_plotfile)
level = 0
lo, hi = amrio.queryDomainCorners(amrID, level)
order = 0

# now get relevant variables thickness and surface
x0, y0, zsurface0 = amrio.readBox2D(amrID, level, lo, hi, 'Z_surface', order)
x0, y0, thk0 = amrio.readBox2D(amrID, level, lo, hi, 'thickness', order)

# downsample temperature and precipitation to resolution of plotfile
plotfile_res = x0[1] - x0[0]
climate = xr.open_dataset('@TEMP') # reads in first NC (in this case, temp)
climate_res = climate.x[1].data - climate.x[0].data

if plotfile_res != climate_res:
    dsi = int(plotfile_res / climate_res)
    base_temp = block_reduce(temp, block_size=(1, dsi, dsi), func=np.mean, cval=np.max(temp))
    base_precip = block_reduce(precip, block_size=(1, dsi, dsi), func=np.mean, cval=np.min(precip))
    base_height = block_reduce(height, block_size=(dsi, dsi), func=np.mean, cval=np.min(height))

# calculate corrections based on lapse rate
    
LRT = - 0.007 # temperature lapse rate (Dolan 2018)
temp_correction = LRT * (zsurface0 - base_height)

b = len(x0)
a = len(y0) # weird that these have to be this way around, but it works
temp_correction_array = np.empty((12, a, b))
for i in range(12):
    temp_correction_array[i, :, :] = temp_correction
temp_corrected = base_temp + temp_correction_array

LRP = @LRP # precipitation lapse rate
precip_corrected = base_precip * np.exp (-LRP * (zsurface0 - base_height))

# run PDD model
pdds = 0.004 # pdd factor snow
pddi = @PDDi # pdd factor ice
pdd = PDDModel(pdd_factor_snow = pdds, pdd_factor_ice = pddi)
pdd_results = pdd(temp_corrected, precip_corrected)
smb = pdd_results['smb']

# save smb to netcdf
Y = x0
X = y0 # again, weird way around but it works
ds = xr.Dataset({'smb': (('x', 'y'), smb)},
                coords={'x': X,
                        'y': Y})
ds.to_netcdf('smb.nc', 'w')