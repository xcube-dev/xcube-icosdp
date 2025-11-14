# The GNU General Public License version 3
# Copyright (C) 2025  by the xcube development team and contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/gpl-3.0.html>.

import xarray as xr
import numpy as np


def _flatten_time_hour(ds: xr.Dataset) -> xr.Dataset:
    times = ds["time"].values
    hours = ds["hour"].values
    date_times = np.array(
        [t + np.timedelta64(int(h), "h") for t in times for h in hours],
        dtype="datetime64[ns]",
    )
    ds_stacked = ds.stack({"time_new": ("time", "hour")})
    ds_stacked = ds_stacked.drop_vars(["time_new", "time", "hour", "hour_bnds"])
    ds_stacked = ds_stacked.rename({"time_new": "time"})
    ds_stacked = ds_stacked.assign_coords({"time": date_times})
    ds_stacked = ds_stacked.transpose("time", "lat", "lon", ...)
    return ds_stacked
