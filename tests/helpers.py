# The MIT License (MIT)
# Copyright (c) 2024-2025 by the xcube development team and contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

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


from xcube.core.store import new_data_store

store = new_data_store("icosdp")
store.describe_data("NEE")
