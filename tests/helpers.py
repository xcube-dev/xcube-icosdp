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

import dask.array as da
import numpy as np
import pandas as pd
import xarray as xr


def get_hourly_005_dataseet():
    # Dimensions
    time = pd.date_range("2001-01-01", "2021-12-31", freq="D")
    hour = np.arange(0, 24, 1)
    lat = np.linspace(89.97, -89.97, 3600)
    lon = np.linspace(-180.0, 180.0, 7200)
    nbnds = 2

    # Build Dataset lazily with Dask
    ds = xr.Dataset(
        data_vars={
            "NEE": (
                ("time", "hour", "lat", "lon"),
                da.zeros(
                    (len(time), len(hour), len(lat), len(lon)),
                    chunks=(1461, 24, 40, 40),  # adjust chunk sizes to taste
                    dtype="float32",
                ),
            ),
            "land_fraction": (
                ("lat", "lon"),
                da.full(
                    (len(lat), len(lon)),
                    fill_value=1.0,
                    chunks=(40, 40),
                    dtype="float64",
                ),
            ),
        },
        coords={
            "time": time,
            "hour": hour,
            "lat": lat,
            "lon": lon,
            "hour_bnds": (("hour", "nbnds"), np.zeros((len(hour), nbnds), dtype=int)),
            "lat_bnds": (("lat", "nbnds"), np.zeros((len(lat), nbnds))),
            "lon_bnds": (("lon", "nbnds"), np.zeros((len(lon), nbnds))),
        },
        attrs={
            "contact": "The FLUXCOM-X team, fluxcomx@bgc-jena.mpg.de",
            "contributor": "Mock contributor",
            "conventions": "CF-1.8",
            "creation_date": "mock",
            "crs": "WGS 84 / Plate Carree",
            "publisher_url": "http://fluxcom.org/",
            "source": "Mock source",
            "time_coverage_start": "2001-01-01T00:00:00",
            "time_coverage_end": "2021-12-31T00:00:00",
        },
    )
    return ds
