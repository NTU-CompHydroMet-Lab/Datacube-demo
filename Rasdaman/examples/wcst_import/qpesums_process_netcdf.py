import h5py
import netCDF4 as nc
import numpy as np
import pandas as pd
import xarray as xr
import time
import os
import sys
from datetime import datetime

def add_time_dimension(input_file):
    # Convert to absolute path
    input_file = os.path.abspath(input_file)
    
    # Ensure input file exists
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file {input_file} not found")
    # Read the original file
    ds = nc.Dataset(input_file)
    
    # Create a new file with '_with_time' suffix
    base_name = os.path.basename(input_file)
    output_name = base_name.replace('.nc', '_with_time.nc')
    output_file = os.path.join(output_dir, output_name)
    ds_new = nc.Dataset(output_file, 'w', format='NETCDF4')
    
    # Extract time from filename (assuming format YYYYMMDD.HHMM)
    time_str = input_file.split('.')[1:3]
    date_str = time_str[0]
    time_str = time_str[1]
    dt = datetime.strptime(f"{date_str}.{time_str}", "%Y%m%d.%H%M")
    timestamp = np.datetime64(dt)
    
    # Create time dimension
    ds_new.createDimension('time', 1)
    time_var = ds_new.createVariable('time', 'f8', ('time',))
    time_var.units = 'seconds since 1970-01-01 00:00:00'
    time_var.calendar = 'standard'
    time_var[:] = nc.date2num(dt, time_var.units, calendar=time_var.calendar)
    
    # Copy all dimensions except time
    for dim_name, dim in ds.dimensions.items():
        ds_new.createDimension(dim_name, len(dim))
    
    # Copy all variables and add time dimension to data variables
    for var_name, var in ds.variables.items():
        # Get the variable attributes
        var_attrs = {attr: var.getncattr(attr) for attr in var.ncattrs()}
        
        # For data variables, add time dimension
        if len(var.dimensions) > 1:  # Assuming data variables have more than 1 dimension
            dims = ('time',) + var.dimensions
            new_var = ds_new.createVariable(var_name, var.dtype, dims)
            new_var[:] = var[np.newaxis, ...]
        else:
            # For coordinate variables, keep original dimensions
            dims = var.dimensions
            new_var = ds_new.createVariable(var_name, var.dtype, dims)
            new_var[:] = var[:]
        
        # Copy variable attributes
        for attr, value in var_attrs.items():
            new_var.setncattr(attr, value)
    
    # Copy global attributes
    ds_new.setncattr('created_by', 'NetCDF time dimension addition script')
    for attr in ds.ncattrs():
        ds_new.setncattr(attr, ds.getncattr(attr))
    
    # Close both datasets
    ds.close()
    ds_new.close()
    
    return output_file

if __name__ == '__main__':
    try:
        # Get the current working directory
        current_dir = os.getcwd()
        print(f"Current working directory: {current_dir}")
        
        # Input file path
        input_file = 'MREF3D21L.20120102.1730.nc'
        if not os.path.exists(input_file):
            print(f"Error: Input file '{input_file}' not found in {current_dir}")
            sys.exit(1)
            
        # Process the file
        output_file = add_time_dimension(input_file)
        print(f"Successfully created file with time dimension: {output_file}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
