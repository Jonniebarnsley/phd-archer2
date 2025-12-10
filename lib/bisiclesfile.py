from pathlib import Path
from xarray import Dataset, DataArray

# NB: amrfile needs the BISICLES AMRfile directory added to PYTHONPATH and the libamrfile directory
# added to LD_LIBRARY_PATH – see my .bashrc for an example
from amrfile import io as amrio

class BisiclesFile:
    """
    A context manager for reading BISICLES AMR HDF5 files.
    
    Provides a Pythonic interface for extracting 2D fields from BISICLES output files
    at different refinement levels. Handles resource management automatically and 
    caches domain corners for efficient multi-level access.
    
    Example:
        with BisiclesFile(file_path) as bf:
            # Read data at different refinement levels
            ds_lev0 = bf.read_dataset('muCoef', lev=0)
            ds_lev1 = bf.read_dataset('muCoef', lev=1)
            
            # Get file timestamp
            time = bf.query_time()
    
    Args:
        file: Path to the BISICLES HDF5 file to read
    """

    def __init__(self, file: Path):
        self.file = file
        self._amrID = None
        self._domain_corners = {}  # Cache domain corners by level

        if not self.exists():
            raise FileNotFoundError(f"BISICLES file not found: {self.file}")

        if self.file.suffix != '.hdf5':
            raise ValueError(f"Invalid file type: {self.file.suffix}. Expected .hdf5")

    @property
    def amrID(self):
        if self._amrID is None:
            try:
                self._amrID = amrio.load(str(self.file))
            except Exception as e:
                print(f"Error loading AMR file: {e}")
                raise
        return self._amrID

    @property
    def attrs(self):
        # default units and long names of BISICLES outputs
        return {
            "thickness"     : {"units": "m",           "long_name": "Ice thickness"},
            "dThickness/dt" : {"units": "m·yr⁻¹",      "long_name": "Thickness rate of change"},
            "xVel"          : {"units": "m·yr⁻¹",      "long_name": "X-velocity"},
            "yVel"          : {"units": "m·yr⁻¹",      "long_name": "Y-velocity"},
            "Z_base"        : {"units": "m",           "long_name": "Bed elevation"},
            "Z_surface"     : {"units": "m",           "long_name": "Surface elevation"},
            "Cwshelf"       : {"units": "Pa·s·m⁻¹",    "long_name": "Basal friction coefficient"},
            "muCoef"        : {"units": "unitless",    "long_name": "Viscosity coefficient"}
            }

    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        """Context manager exit - release memory"""
        self.close()

    def exists(self):
        return self.file.exists()

    def close(self):
        """Release memory"""
        if self._amrID is not None:
            amrio.free(self._amrID)
            self._amrID = None

    def query_time(self) -> float:
        """Query the time from the AMR file"""
        time = amrio.queryTime(self.amrID)
        return round(time, 2)

    def domain_corners(self, level: int) -> tuple:
        """Get domain corners for a specific level, cached for efficiency"""
        if level not in self._domain_corners:
            lo, hi = amrio.queryDomainCorners(self.amrID, level)
            self._domain_corners[level] = (lo, hi)
        return self._domain_corners[level]

    def read_dataarray(self, variable: str, lev: int=0, order: int=0) -> DataArray:
        """Extract 2D data array from AMR file and return as xarray DataArray"""
        
        lo, hi = self.domain_corners(lev)
        x0, y0, field = amrio.readBox2D(self.amrID, lev, lo, hi, variable, order)
        data_array = DataArray(
            data = field,
            dims = ['y', 'x'],
            coords = {'x': x0, 'y': y0},
            attrs = self.attrs.get(variable, {})
        )
        return data_array

    def read_dataset(self, variables: list, lev: int=0, order: int=0) -> Dataset:
        """Extract multiple variables from AMR file and return as xarray Dataset"""
        
        flat_data = {}
        for var in variables:
            variable_name = var.replace("/", "")  # can't have / in netcdf variable names
            flat_data[variable_name] = self.read_dataarray(var, lev=lev, order=order)
        ds = Dataset(flat_data)
        return ds