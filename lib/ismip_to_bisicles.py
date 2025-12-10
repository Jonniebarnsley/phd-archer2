import numpy as np
from pathlib import Path
import xarray as xr
from xarray.coders import CFDatetimeCoder

def separate_levels(ds: xr.Dataset) -> xr.Dataset:
    data = {}
    for i, z in enumerate(ds.z):
        data[f'thermal_forcing_00{i:02d}'] = ds.sel(z=z).thermal_forcing.drop_vars(['z', 'time'])
    return xr.Dataset(data, coords={'x': ds.x, 'y': ds.y})

def regrid_to_bisicles(ds: xr.Dataset) -> xr.Dataset:

    bisicles_8km_x = np.arange(4.000e+3, 6.148e+06, 8.000e+3)
    bisicles_centered = bisicles_8km_x - bisicles_8km_x.mean()

    # pad until dataset exceeds the extent of bisicles
    N = 10 # any big enough number will do
    padded = ds.pad(x=(N, N), y=(N, N))

    x = ds.x
    dx = x[1] - x[0]
    padded_axis_vals = np.arange(x.min() - N*dx, x.max()+N*dx+1, dx)
    padded['x'] = padded_axis_vals
    padded['y'] = padded_axis_vals

    # interpolate onto centered bisicles grid
    ds_bisicles = ds.interp(x=bisicles_centered, y=bisicles_centered)

    # revert to un-centered grid
    ds_bisicles['x'] = bisicles_8km_x
    ds_bisicles['y'] = bisicles_8km_x

    return ds_bisicles

def ismip_to_bisicles(filepath: Path) -> None:

    info = filepath.name.split('_')
    model = info[0]
    scenario = info[1]

    coder = CFDatetimeCoder(use_cftime=True)
    ds = xr.open_dataset(filepath, decode_times=coder)

    for cfyear in ds.time.values:
        year = cfyear.year
        outfile = Path('bisicles_compatible') / f'{model}_{scenario}_thermal_forcing_8km_x_60m_{year}.nc'

        if outfile.exists():
            continue

        print(year)
        timeslice = ds.sel(time=cfyear)
        timeslice = regrid_to_bisicles(timeslice)
        timeslice = separate_levels(timeslice)
        timeslice = timeslice.fillna(0)

        try:
            timeslice.to_netcdf(outfile)
        except KeyboardInterrupt:
            outfile.unlink(missing_ok=True)
            raise
        except Exception as e:
            print(f'Encountered an error whilst writing file: {e}')
            outfile.unlink(missing_ok=True)

def main():
    
    outdir = Path('bisicles_compatible')
    outdir.mkdir(exist_ok=True)
    
    pwd = Path('.')
    files = pwd.glob('*_thermal_forcing_8km_x_60m_*.nc')

    for f in sorted(files):
        print(f'---> Dividing up {f.name} into years...')
        ismip_to_bisicles(f)

if __name__ == '__main__':
    main()

    
