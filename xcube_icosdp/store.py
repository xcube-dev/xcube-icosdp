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
)
from xcube.core.chunk import chunk_dataset
from xcube.util.jsonschema import (
    JsonArraySchema,
    JsonDateSchema,
    JsonNumberSchema,
    JsonObjectSchema,
    JsonStringSchema,
)

from .constants import ICOSDP_DATA_OPENER_ID, MAPPING_NONAGG_DATA_ID_URI


class IcosdpDataStore(DataStore):
    """Implementation of the ICOS Data Portal data store."""

    def __init__(
        self,
        email: str = None,
        password: str = None,
    ):
        self.meta = None
        self.data = None
        if email and password:
            self.meta, self.data = icoscp_core.icos.bootstrap.fromCredentials(
                email, password
            )

    @classmethod
    def get_data_store_params_schema(cls) -> JsonObjectSchema:
        params = dict(
            email=JsonStringSchema(
                title="E-mail address of ICOS user account",
                description="E-mail used when signing in at https://cpauth.icos-cp.eu/login/",
            ),
            password=JsonStringSchema(
                title="Password of ICOS user account",
                description="Password used when signing in at https://cpauth.icos-cp.eu/login/",
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
        data_ids = list(MAPPING_NONAGG_DATA_ID_URI.keys())
        for data_id in data_ids:
            yield data_id

    def has_data(self, data_id: str, data_type: str = None) -> bool:
        return data_id in MAPPING_NONAGG_DATA_ID_URI

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
            aggregation=JsonStringSchema(
                title="Aggregation mode",
                description="Note that '005_hourly' is the non-aggregated dataset.",
                enum=[
                    "005_hourly",
                    # "050_monthly",
                    # "025_monthlycycle",
                    # "025_daily",
                    # "005_monthly",
                ],
                default="005_hourly",
            ),
            time_range=JsonDateSchema.new_range(
                min_date="2001-01-01", max_date="2021-12-31", nullable=True
            ),
            bbox=JsonArraySchema(
                title="Bounding box [west, south, east, north] in degree",
                items=(
                    JsonNumberSchema(minimum=-180, maximum=180),
                    JsonNumberSchema(minimum=-90, maximum=90),
                    JsonNumberSchema(minimum=-180, maximum=180),
                    JsonNumberSchema(minimum=-90, maximum=90),
                ),
            ),
        )
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
    ) -> xr.Dataset:
        self._assert_has_data(data_id, data_type=data_type)
        self._assert_valid_data_type(data_type)
        self._assert_valid_opener_id(opener_id)
        schema = self.get_open_data_params_schema(data_id=data_id, opener_id=opener_id)
        schema.validate_instance(open_params)

        agg_mode = open_params.get("aggregation", "005_hourly")
        if agg_mode == "005_hourly":
            ds = xr.open_dataset(
                MAPPING_NONAGG_DATA_ID_URI[data_id], engine="zarr", chunks={}
            )
            ds = ds.unify_chunks()
            chunks = {str(dim): sizes[0] for dim, sizes in ds.chunksizes.items()}
            time_range = open_params.get("time_range")
            if time_range:
                dt_start = np.datetime64(time_range[0], "ns")
                dt_end = np.datetime64(time_range[1], "ns")
                if dt_end <= dt_start:
                    raise DataStoreError(
                        f"Invalid time range {time_range!r}. Start date must be before end date."
                    )
                ds = ds.sel(time=slice(dt_start, dt_end))
            bbox = open_params.get("bbox")
            if bbox:
                if bbox[0] >= bbox[2] or bbox[1] >= bbox[3]:
                    raise DataStoreError(
                        f"Invalid bbox {bbox!r}. West must be smaller East and South must be smaller West."
                    )
                ds = ds.sel(lat=slice(bbox[3], bbox[1]), lon=slice(bbox[0], bbox[2]))
            if time_range or bbox:
                ds = chunk_dataset(ds, chunks, format_name="zarr")
        else:
            raise DataStoreError(
                "Only aggregation mode '005_hourly' supported so far. "
            )
        return ds

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
