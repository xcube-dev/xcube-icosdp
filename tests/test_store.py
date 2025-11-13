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


import unittest
from unittest.mock import patch

import xarray as xr
from xcube.core.store import (
    DatasetDescriptor,
    DataStoreError,
    get_data_store_params_schema,
    new_data_store,
)
from xcube.util.jsonschema import JsonObjectSchema

from xcube_icosdp.constants import DATA_STORE_ID

from .helpers import get_hourly_005_dataseet


class IcosdpDataStoreTest(unittest.TestCase):

    def test_get_data_store_params_schema(self):
        schema = get_data_store_params_schema(DATA_STORE_ID)
        self.assertIsInstance(schema, JsonObjectSchema)
        self.assertIn("email", schema.properties)
        self.assertIn("password", schema.properties)
        self.assertNotIn("key", schema.properties)
        self.assertNotIn("email", schema.required)

    def test_get_data_types(self):
        store = new_data_store(DATA_STORE_ID)
        self.assertCountEqual(("dataset",), store.get_data_types())

    def test_get_data_types_for_data(self):
        store = new_data_store(DATA_STORE_ID)
        self.assertCountEqual(("dataset",), store.get_data_types_for_data("NEE"))

    def test_get_data_ids(self):
        store = new_data_store(DATA_STORE_ID)
        self.assertCountEqual(
            [
                "FLUXCOM-X-BASE_NEE",
                "FLUXCOM-X-BASE_GPP",
                "FLUXCOM-X-BASE_ET",
                "FLUXCOM-X-BASE_ET_T",
            ],
            store.get_data_ids(),
        )

    def test_has_data(self):
        store = new_data_store(DATA_STORE_ID)
        self.assertTrue(store.has_data("FLUXCOM-X-BASE_NEE"))
        self.assertTrue(store.has_data("FLUXCOM-X-BASE_GPP"))
        self.assertFalse(store.has_data("FLUXCOM-X-BASE_NEE2"))

    @patch("xarray.open_dataset")
    def test_describe_data(self, mock_open_dataset):
        mock_open_dataset.return_value = get_hourly_005_dataseet()
        store = new_data_store(DATA_STORE_ID)
        descriptor = store.describe_data("FLUXCOM-X-BASE_NEE")
        mock_open_dataset.assert_called_once_with(
            (
                "https://swift.dkrz.de/v1/dkrz_a1e106384d7946408b9724b59858a536/"
                "fluxcom-x/FLUXCOMxBase/NEE"
            ),
            engine="zarr",
            chunks={},
        )
        self.assertIsInstance(descriptor, DatasetDescriptor)
        self.assertEqual("FLUXCOM-X-BASE_NEE", descriptor.data_id)
        self.assertEqual("dataset", descriptor.data_type.alias)
        self.assertEqual("EPSG:4326", descriptor.crs)
        self.assertEqual((-180, -90, 180, 90), descriptor.bbox)
        self.assertEqual(
            ("2001-01-01T00:00:00Z", "2021-12-31T00:00:00Z"), descriptor.time_range
        )

    def test_get_data_opener_ids(self):
        store = new_data_store(DATA_STORE_ID)
        self.assertEqual(("dataset:zarr:icosdp",), store.get_data_opener_ids())

    def test_get_open_data_params_schema(self):
        store = new_data_store(DATA_STORE_ID)
        schema = store.get_open_data_params_schema()
        self.assertIsInstance(schema, JsonObjectSchema)
        self.assertIn("time_range", schema.properties)
        self.assertIn("bbox", schema.properties)

    @patch("xarray.open_dataset")
    def test_open_data(self, mock_open_dataset):
        mock_open_dataset.return_value = get_hourly_005_dataseet()
        store = new_data_store(DATA_STORE_ID)

        # default
        ds = store.open_data("FLUXCOM-X-BASE_NEE")
        self.assertIsInstance(ds, xr.Dataset)
        self.assertCountEqual(["NEE", "land_fraction"], list(ds.data_vars))
        self.assertEqual((7670, 24, 3600, 7200), ds["NEE"].shape)
        self.assertEqual((3600, 7200), ds["land_fraction"].shape)
        mock_open_dataset.assert_called_once_with(
            (
                "https://swift.dkrz.de/v1/dkrz_a1e106384d7946408b9724b59858a536/"
                "fluxcom-x/FLUXCOMxBase/NEE"
            ),
            engine="zarr",
            chunks={},
        )

        # sub-setting with opening parameters
        ds = store.open_data(
            "FLUXCOM-X-BASE_NEE",
            time_range=("2002-01-01", "2002-12-31"),
            bbox=[0, 40, 10, 50],
        )
        self.assertIsInstance(ds, xr.Dataset)
        self.assertCountEqual(["NEE", "land_fraction"], list(ds.data_vars))
        self.assertEqual((365, 24, 200, 200), ds["NEE"].shape)
        self.assertEqual((200, 200), ds["land_fraction"].shape)

        # invalid time_range
        with self.assertRaises(DataStoreError) as cm:
            _ = store.open_data(
                "FLUXCOM-X-BASE_NEE", time_range=("2004-01-01", "2002-12-31")
            )
        self.assertIn("Invalid time range ", f"{cm.exception}")

        # invalid bbox
        with self.assertRaises(DataStoreError) as cm:
            _ = store.open_data("FLUXCOM-X-BASE_NEE", bbox=(0, 45, 10, 40))
        self.assertIn("Invalid bbox ", f"{cm.exception}")

    def test_search_data(self):
        store = new_data_store(DATA_STORE_ID)
        with self.assertRaises(NotImplementedError) as context:
            store.search_data()
        self.assertEqual(
            "search_data() operation is not supported.", str(context.exception)
        )

    def test_assert_has_data(self):
        store = new_data_store(DATA_STORE_ID)
        with self.assertRaises(DataStoreError) as cm:
            _ = store._assert_has_data("NEE2")
        self.assertIn("Data id 'NEE2' is not available. ", f"{cm.exception}")

    def test_assert_valid_data_type(self):
        store = new_data_store(DATA_STORE_ID)
        with self.assertRaises(DataStoreError) as cm:
            _ = store._assert_valid_data_type("mldataset")
        self.assertIn("Data type must be one of ", f"{cm.exception}")

    def test_assert_valid_opener_id(self):
        store = new_data_store(DATA_STORE_ID)
        with self.assertRaises(DataStoreError) as cm:
            _ = store._assert_valid_opener_id("dataset:zarr:https")
        self.assertIn("Data opener identifier must be one of ", f"{cm.exception}")
