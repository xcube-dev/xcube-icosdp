# The MIT License (MIT)
# Copyright (c) 2025 by the xcube development team and contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.


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
        self.assertCountEqual(["NEE", "GPP", "ET", "ET_T"], store.get_data_ids())

    def test_has_data(self):
        store = new_data_store(DATA_STORE_ID)
        self.assertTrue(store.has_data("NEE"))
        self.assertTrue(store.has_data("GPP"))
        self.assertFalse(store.has_data("GPP2"))

    @patch("xarray.open_dataset")
    def test_describe_data(self, mock_open_dataset):
        mock_open_dataset.return_value = get_hourly_005_dataseet()
        store = new_data_store(DATA_STORE_ID)
        descriptor = store.describe_data("NEE")
        mock_open_dataset.assert_called_once_with(
            (
                "https://swift.dkrz.de/v1/dkrz_a1e106384d7946408b9724b59858a536/"
                "fluxcom-x/FLUXCOMxBase/NEE"
            ),
            engine="zarr",
            chunks={},
        )
        self.assertIsInstance(descriptor, DatasetDescriptor)
        self.assertEqual("NEE", descriptor.data_id)
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
        self.assertIn("aggregation", schema.properties)
        self.assertIn("time_range", schema.properties)
        self.assertIn("bbox", schema.properties)

    @patch("xarray.open_dataset")
    def test_open_data(self, mock_open_dataset):
        mock_open_dataset.return_value = get_hourly_005_dataseet()
        store = new_data_store(DATA_STORE_ID)

        # default
        ds = store.open_data("NEE")
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
            "NEE", time_range=("2002-01-01", "2002-12-31"), bbox=[0, 40, 10, 50]
        )
        self.assertIsInstance(ds, xr.Dataset)
        self.assertCountEqual(["NEE", "land_fraction"], list(ds.data_vars))
        self.assertEqual((365, 24, 200, 200), ds["NEE"].shape)
        self.assertEqual((200, 200), ds["land_fraction"].shape)

        # invalid time_range
        with self.assertRaises(DataStoreError) as cm:
            _ = store.open_data("NEE", time_range=("2004-01-01", "2002-12-31"))
        self.assertIn("Invalid time range ", f"{cm.exception}")

        # invalid bbox
        with self.assertRaises(DataStoreError) as cm:
            _ = store.open_data("NEE", bbox=(0, 45, 10, 40))
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
