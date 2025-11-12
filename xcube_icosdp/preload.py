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

import re

import fsspec
import icoscp_core
import xarray as xr
from xcube.core.chunk import chunk_dataset
from xcube.core.store import DataStoreError, PreloadedDataStore, new_data_store
from xcube.core.store.preload import ExecutorPreloadHandle, PreloadState, PreloadStatus

from .constants import TEMP_PROCESSING_FOLDER, FluxcomBaseDataIdsUri

_CHUNK_SIZE = 1024 * 1024


class IcosdpPreloadHandle(ExecutorPreloadHandle):

    # noinspection PyUnresolvedReferences
    def __init__(
        self,
        cache_store: PreloadedDataStore,
        icos_meta: icoscp_core.metaclient.MetadataClient,
        icos_data: icoscp_core.dataclient.DataClient,
        *data_ids: str,
        **preload_params,
    ):
        self._icos_meta = icos_meta
        self._icos_data = icos_data

        # setup cache store
        self._cache_store = cache_store
        self._cache_fs: fsspec.AbstractFileSystem = self._cache_store.fs
        self._cache_root = self._cache_store.root

        # setup processing store
        # noinspection PyProtectedMember
        self._process_store = new_data_store("file", root=TEMP_PROCESSING_FOLDER)
        self._process_fs: fsspec.AbstractFileSystem = self._process_store.fs
        self._process_root = self._process_store.root
        self._clean_up()
        self._process_fs.makedirs(self._process_root, exist_ok=True)

        # all new defaults for xarray confine functions to mute warnings
        xr.set_options(use_new_combine_kwarg_defaults=True)

        # trigger preload in parent class
        self._data_ids = data_ids
        super().__init__(data_ids=data_ids, **preload_params)

    def close(self) -> None:
        self._clean_up()

    def preload_data(self, data_id: str, **preload_params):
        uri = FluxcomBaseDataIdsUri.datasets[data_id].agg_mode[
            preload_params["agg_mode"]
        ]
        meta_years = self._icos_meta.get_collection_meta(uri).members

        # temporal selection
        if "time_range" in preload_params:
            time_range = preload_params["time_range"]
            year_start = int(time_range[0].split("-")[0])
            year_end = int(time_range[1].split("-")[0])
            years = [year for year in range(year_start, year_end + 1)]
            meta_years = [
                meta_year
                for meta_year in meta_years
                if int(meta_year.title.split(" ")[-1]) in years
            ]
            if not meta_years:
                raise DataStoreError(f"No data found for {time_range}.")

        # download data
        self.notify(
            PreloadState(
                data_id,
                status=PreloadStatus.started,
                progress=0.0,
                message="Download in progress",
            )
        )
        num_file = len(meta_years)
        for i, meta_year in enumerate(meta_years):
            year_objs = self._icos_meta.get_collection_meta(meta_year.res).members
            spatial_res, freq = preload_params["agg_mode"].split("_")
            spatial_res = str(int(spatial_res) / 100)
            if freq == "monthlycycle":
                freq_sel = "monthly diurnal cycle"
            else:
                freq_sel = freq
            year_objs_sel = [
                year_obj
                for year_obj in year_objs
                if spatial_res in year_obj.name and freq_sel in year_obj.name
            ]
            assert len(year_objs_sel) == 1
            year_obj = year_objs_sel[0]
            self._icos_data.save_to_folder(year_obj.res, self._process_root)
            self.notify(PreloadState(data_id, progress=0.6 * (i + 1) / num_file))

        # build cube
        self.notify(
            PreloadState(
                data_id,
                progress=0.6,
                message="Prepare data",
            )
        )
        var_name = data_id.replace("FLUXCOM-X-BASE_", "")
        data_ids_temp = self._process_store.list_data_ids()
        pattern = re.compile(rf"^{var_name}_[0-9]{{4}}")
        data_ids_sel = [did for did in data_ids_temp if re.match(pattern, did)]
        dss = []
        for did in data_ids_sel:
            ds = self._process_store.open_data(did, chunks={})
            dss.append(ds)
        ds = xr.concat(dss, dim="time")
        bbox = preload_params.get("bbox")
        if bbox:
            if bbox[0] >= bbox[2] or bbox[1] >= bbox[3]:
                raise DataStoreError(
                    f"Invalid bbox {bbox!r}. West must be smaller East and South must "
                    f"be smaller North."
                )
            ds = ds.sel(lat=slice(bbox[3], bbox[1]), lon=slice(bbox[0], bbox[2]))

        # write cube
        format_id = preload_params.get("format_id", "zarr")
        if "chunks" in preload_params:
            chunks = {
                str(dim): chunk
                for (dim, chunk) in zip(ds.dims, preload_params["chunks"])
            }
            ds = chunk_dataset(ds, chunks, format_name=format_id)
        data_id_out = f"{var_name}_{freq}"
        if "time_range" in preload_params:
            data_id_out += f"_{year_start}_{year_end}"
        if format_id == "netcdf":
            data_id_out += ".nc"
        else:
            data_id_out += ".zarr"
        self.notify(
            PreloadState(
                data_id,
                progress=0.7,
                message="Write data",
            )
        )
        self._cache_store.write_data(ds, data_id_out, replace=True)
        self.notify(PreloadState(data_id, progress=1.0, message="Preload finished"))

        # delete temp storage
        self._clean_up()

    def _clean_up(self) -> None:
        if self._process_fs.isdir(self._process_root):
            self._process_fs.rm(self._process_root, recursive=True)
