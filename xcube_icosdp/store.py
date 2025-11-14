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

from typing import Any, Container, Iterator, Tuple

import icoscp_core.icos
import numpy as np
import pandas as pd
import xarray as xr
from xcube.core.store import (
    DataDescriptor,
    DatasetDescriptor,
    DataStore,
    DataStoreError,
    DataType,
    DataTypeLike,
    PreloadedDataStore,
    new_data_store,
)
from xcube.util.jsonschema import (
    JsonArraySchema,
    JsonBooleanSchema,
    JsonIntegerSchema,
    JsonObjectSchema,
    JsonStringSchema,
)

from .constants import (
    CACHE_FOLDER_NAME,
    ICOSDP_DATA_OPENER_ID,
    SPATIOTEMPORAL_PARAMS,
    FluxcomBaseDataIdsUri,
)
from .preload import IcosdpPreloadHandle
from .utils import _flatten_time_hour


class IcosdpDataStore(DataStore):
    """Implementation of the ICOS Data Portal data store."""

    def __init__(
        self,
        email: str = None,
        password: str = None,
        cache_store_id: str = "file",
        cache_store_params: dict = None,
    ):
        self._icos_meta = None
        self._icos_data = None
        if email and password:
            self._icos_meta, self._icos_data = (
                icoscp_core.icos.bootstrap.fromCredentials(email, password)
            )
        # cache store for preloaded datasets
        if cache_store_params is None:
            cache_store_params = dict(root=CACHE_FOLDER_NAME)
        cache_store_params["max_depth"] = cache_store_params.pop("max_depth", 10)
        self.cache_store: PreloadedDataStore = new_data_store(
            cache_store_id, **cache_store_params
        )

    @classmethod
    def get_data_store_params_schema(cls) -> JsonObjectSchema:
        params = dict(
            email=JsonStringSchema(
                title="E-mail address of ICOS user account",
                description=(
                    "E-mail used when signing in at https://cpauth.icos-cp.eu/login/. "
                    "This is only needed if the aggregated datasets want to be "
                    "accessed via `preload_data`."
                ),
            ),
            password=JsonStringSchema(
                title="Password of ICOS user account",
                description=(
                    "Password used when signing in at https://cpauth.icos-cp.eu/login/. "
                    "This is only needed if the aggregated datasets want to be "
                    "accessed via `preload_data`."
                ),
            ),
            cache_store_id=JsonStringSchema(
                title="Store ID of cache data store.",
                description=(
                    "The cache data store is a filesystem-based data store implemented "
                    "in xcube, which is used to store the preloaded data."
                ),
                default="file",
            ),
            cache_store_params=JsonObjectSchema(
                title="Store parameters of cache data store.",
                description=(
                    "The available parameters can be viewed using "
                    "`get_data_store_params_schema(cache_store_id)`."
                ),
                default=dict(root=CACHE_FOLDER_NAME, max_depth=10),
            ),
        )
        return JsonObjectSchema(
            properties=dict(**params),
            required=[],
            additional_properties=False,
        )

    @classmethod
    def get_data_types(cls) -> Tuple[str, ...]:
        return ("dataset",)

    def get_data_types_for_data(self, data_id: str) -> Tuple[str, ...]:
        return ("dataset",)

    def get_data_ids(
        self, data_type: DataTypeLike = None, include_attrs: Container[str] = None
    ) -> Iterator[str | tuple[str, dict[str, Any]] | None]:
        data_ids = FluxcomBaseDataIdsUri.datasets.keys()
        for data_id in data_ids:
            yield data_id

    def has_data(self, data_id: str, data_type: str = None) -> bool:
        return data_id in FluxcomBaseDataIdsUri.datasets.keys()

    def describe_data(
        self, data_id: str, data_type: DataTypeLike = None
    ) -> DataDescriptor:
        self._assert_valid_data_type(data_type)
        ds = self.open_data(data_id)
        schema = self.get_open_data_params_schema(data_id=data_id)
        return DatasetDescriptor(
            data_id,
            crs="EPSG:4326",
            bbox=(-180, -90, 180, 90),
            time_range=(
                pd.to_datetime(ds.time[0].item()).strftime("%Y-%m-%dT%H:%M:%SZ"),
                pd.to_datetime(ds.time[-1].item()).strftime("%Y-%m-%dT%H:%M:%SZ"),
            ),
            dims={str(k): int(v) for k, v in ds.sizes.items()},
            attrs=ds.attrs,
            open_params_schema=schema,
        )

    def get_data_opener_ids(
        self, data_id: str = None, data_type: DataTypeLike = None
    ) -> Tuple[str, ...]:
        return (ICOSDP_DATA_OPENER_ID,)

    def get_open_data_params_schema(
        self, data_id: str = None, opener_id: str = None
    ) -> JsonObjectSchema:
        params = dict(
            flatten_time=JsonBooleanSchema(
                title="Flatten time and hour dimensions",
                description=(
                    "If enabled, combines the 'time' and 'hour' dimensions into a "
                    "single datetime axis."
                ),
                default=False,
            ),
        )
        params.update(SPATIOTEMPORAL_PARAMS)
        return JsonObjectSchema(
            properties=dict(**params),
            required=[],
            additional_properties=False,
        )

    def open_data(
        self,
        data_id: str,
        opener_id: str = None,
        data_type: DataTypeLike = None,
        **open_params,
    ) -> xr.Dataset | DataStoreError:
        self._assert_has_data(data_id, data_type=data_type)
        self._assert_valid_data_type(data_type)
        self._assert_valid_opener_id(opener_id)
        schema = self.get_open_data_params_schema(data_id=data_id, opener_id=opener_id)
        schema.validate_instance(open_params)

        ds = xr.open_dataset(
            FluxcomBaseDataIdsUri.datasets[data_id].agg_mode["005_hourly"],
            engine="zarr",
            chunks={},
        )
        ds = ds.unify_chunks()
        time_range = open_params.get("time_range")
        if time_range:
            dt_start = np.datetime64(time_range[0], "ns")
            dt_end = np.datetime64(time_range[1], "ns")
            if dt_end <= dt_start:
                raise DataStoreError(
                    f"Invalid time range {time_range!r}. "
                    f"Start date must be before end date."
                )
            ds = ds.sel(time=slice(dt_start, dt_end))
        bbox = open_params.get("bbox")
        if bbox:
            if bbox[0] >= bbox[2] or bbox[1] >= bbox[3]:
                raise DataStoreError(
                    f"Invalid bbox {bbox!r}. West must be smaller than East and "
                    f"South must be smaller than North."
                )
            ds = ds.sel(lat=slice(bbox[3], bbox[1]), lon=slice(bbox[0], bbox[2]))
        if open_params.get("flatten_time", False):
            ds = _flatten_time_hour(ds)
        return ds

    def preload_data(self, *data_ids: str, **preload_params) -> PreloadedDataStore:
        if not data_ids:
            raise ValueError("At least one `data_id` must be provided.")

        schema = self.get_preload_data_params_schema()
        schema.validate_instance(preload_params)

        if self._icos_meta is None:
            raise DataStoreError(
                "To preload the aggregated datasets, please provide e-mail and "
                "password of your ICOS account when initiating the data store with "
                "`new_data_store('icosdp', email='xxx', password='xxx')`"
            )

        self.cache_store.preload_handle = IcosdpPreloadHandle(
            self.cache_store,
            self._icos_meta,
            self._icos_data,
            *data_ids,
            **preload_params,
        )
        return self.cache_store

    def get_preload_data_params_schema(self) -> JsonObjectSchema:
        params = dict(
            agg_mode=JsonStringSchema(
                title="Aggregation mode",
                description=(
                    "Four aggregation modes are published in the ICOS FLUXCOM-X-BASE "
                    "collection. View e.g. https://meta.icos-cp.eu/collections/vvQKmP2OJRY-B-vIl-YXIHFs"
                ),
                enum=[
                    "050_monthly",
                    "025_monthlycycle",
                    "025_daily",
                    "005_monthly",
                ],
            ),
            flatten_time=JsonBooleanSchema(
                title="Flatten time and hour dimensions",
                description=(
                    "If enabled, combines the 'time' and 'hour' dimensions into a "
                    "single datetime axis. This option is available only when "
                    "`agg_mode='025_monthlycycle'`."
                ),
                default=False,
            ),
            blocking=JsonBooleanSchema(
                title="Switch to make the preloading process blocking or "
                "non-blocking",
                description="If True, the preloading process blocks the script.",
                default=True,
            ),
            silent=JsonBooleanSchema(
                title="Switch to visualize the preloading process.",
                description=(
                    "If False, the preloading progress will be visualized in a table."
                    "If True, the visualization will be suppressed."
                ),
                default=True,
            ),
            target_format=JsonStringSchema(
                title="Format of the preloaded dataset in the cache.",
                enum=["zarr", "netcdf"],
                default="zarr",
            ),
            chunks=JsonArraySchema(
                title="Chunk sizes for each dimension of the preloaded datasets.",
                description="An iterable with length same as number of dimensions.",
                items=JsonIntegerSchema(),
            ),
        )
        params.update(SPATIOTEMPORAL_PARAMS)
        return JsonObjectSchema(
            properties=dict(**params),
            required=["agg_mode"],
            additional_properties=False,
        )

    def search_data(self, data_type: DataTypeLike = None, **search_params):
        schema = self.get_search_params_schema()
        schema.validate_instance(search_params)
        raise NotImplementedError("search_data() operation is not supported.")

    @classmethod
    def get_search_params_schema(
        cls, data_type: DataTypeLike = None
    ) -> JsonObjectSchema:
        return JsonObjectSchema(
            properties={},
            required=[],
            additional_properties=False,
        )

    # Auxiliary functions
    def _assert_has_data(self, data_id: str, data_type: str = None) -> None:
        if not self.has_data(data_id, data_type=data_type):
            raise DataStoreError(
                f"Data id {data_id!r} is not available. The store has the following "
                f"data ids {self.list_data_ids()!r}."
            )

    def _is_valid_data_type(self, data_type: DataTypeLike) -> bool:
        return data_type is None or any(
            DataType.normalize(data_type_str).is_super_type_of(data_type)
            for data_type_str in self.get_data_types()
        )

    def _assert_valid_data_type(self, data_type: DataTypeLike) -> None:
        if not self._is_valid_data_type(data_type):
            raise DataStoreError(
                f"Data type must be one of {self.get_data_types()!r}, "
                f"but got {data_type!r}."
            )

    def _assert_valid_opener_id(self, opener_id: str) -> None:
        if opener_id is not None and opener_id is not ICOSDP_DATA_OPENER_ID:
            raise DataStoreError(
                f"Data opener identifier must be one of "
                f"{self.get_data_opener_ids()}, but got {opener_id!r}."
            )
