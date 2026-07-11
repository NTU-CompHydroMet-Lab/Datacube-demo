from netCDF4 import Dataset
import numpy as np

src = Dataset("/tmp/era5/tp_201909.nc")
lat = src.variables["latitude"][:]      # descending 90..-90
lon = src.variables["longitude"][:]     # 0..359.75
tvar = src.variables["valid_time"]

# Taiwan bbox
la0, la1 = 20.0, 27.0
lo0, lo1 = 118.0, 123.5
lat_idx = np.where((lat >= la0) & (lat <= la1))[0]
lon_idx = np.where((lon >= lo0) & (lon <= lo1))[0]
la_s = slice(int(lat_idx[0]), int(lat_idx[-1]) + 1)
lo_s = slice(int(lon_idx[0]), int(lon_idx[-1]) + 1)
NT = 24  # first 24 hourly steps

out = Dataset("/tmp/era5/tp_tw_small.nc", "w", format="NETCDF4_CLASSIC")
out.createDimension("valid_time", NT)
out.createDimension("latitude", la_s.stop - la_s.start)
out.createDimension("longitude", lo_s.stop - lo_s.start)

vt = out.createVariable("valid_time", "f8", ("valid_time",))
vt.units = tvar.units
vt.calendar = getattr(tvar, "calendar", "standard")
vt[:] = tvar[0:NT]

vlat = out.createVariable("latitude", "f4", ("latitude",))
vlat.units = "degrees_north"
vlat[:] = lat[la_s]

vlon = out.createVariable("longitude", "f4", ("longitude",))
vlon.units = "degrees_east"
vlon[:] = lon[lo_s]

vtp = out.createVariable("tp", "f4", ("valid_time", "latitude", "longitude"))
vtp.units = "m"
vtp[:] = src.variables["tp"][0:NT, la_s, lo_s]
out.close()

la = lat[la_s]; lo = lon[lo_s]
print("wrote /tmp/era5/tp_tw_small.nc")
print("shape:", NT, la.size, lo.size)
print("lat:", float(la[0]), "->", float(la[-1]), "res", float(la[1]-la[0]))
print("lon:", float(lo[0]), "->", float(lo[-1]), "res", float(lo[1]-lo[0]))
