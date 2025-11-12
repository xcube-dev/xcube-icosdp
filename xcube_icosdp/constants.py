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

import logging
from dataclasses import dataclass

from xcube.util.jsonschema import (
    JsonArraySchema,
    JsonDateSchema,
    JsonNumberSchema,
    JsonStringSchema,
)

DATA_STORE_ID = "icosdp"
LOG = logging.getLogger("xcube.icosdp")
ICOSDP_DATA_OPENER_ID = "dataset:zarr:icosdp"

CACHE_FOLDER_NAME = "icospd_cache"
TEMP_PROCESSING_FOLDER = "icosdp_temp"


@dataclass
class FluxcomDataset:
    """Represents all aggregation modes for a Fluxcom variable."""

    agg_mode: dict[str, str]


class FluxcomBaseDataIdsUri:
    """Container for all Fluxcom variables and their aggregation modes."""

    datasets: dict[str, FluxcomDataset] = {
        "FLUXCOM-X-BASE_NEE": FluxcomDataset(
            agg_mode={
                "005_hourly": "https://swift.dkrz.de/v1/dkrz_a1e106384d7946408b9724b59858a536/fluxcom-x/FLUXCOMxBase/NEE",
                "050_monthly": "https://meta.icos-cp.eu/collections/X_-p994BqVSG6nWJkeK1ALjW",
                "025_monthlycycle": "https://meta.icos-cp.eu/collections/X_-p994BqVSG6nWJkeK1ALjW",
                "025_daily": "https://meta.icos-cp.eu/collections/X_-p994BqVSG6nWJkeK1ALjW",
                "005_monthly": "https://meta.icos-cp.eu/collections/X_-p994BqVSG6nWJkeK1ALjW",
            }
        ),
        "FLUXCOM-X-BASE_GPP": FluxcomDataset(
            agg_mode={
                "005_hourly": "https://swift.dkrz.de/v1/dkrz_a1e106384d7946408b9724b59858a536/fluxcom-x/FLUXCOMxBase/GPP",
                "050_monthly": "https://meta.icos-cp.eu/collections/AYj7-lwcdCLnBXJDoscxQZou",
                "025_monthlycycle": "https://meta.icos-cp.eu/collections/AYj7-lwcdCLnBXJDoscxQZou",
                "025_daily": "https://meta.icos-cp.eu/collections/AYj7-lwcdCLnBXJDoscxQZou",
                "005_monthly": "https://meta.icos-cp.eu/collections/AYj7-lwcdCLnBXJDoscxQZou",
            }
        ),
        "FLUXCOM-X-BASE_ET": FluxcomDataset(
            agg_mode={
                "005_hourly": "https://swift.dkrz.de/v1/dkrz_a1e106384d7946408b9724b59858a536/fluxcom-x/FLUXCOMxBase/ET",
                "050_monthly": "https://meta.icos-cp.eu/collections/_l85vWiIV81AifoxCkty50YI",
                "025_monthlycycle": "https://meta.icos-cp.eu/collections/_l85vWiIV81AifoxCkty50YI",
                "025_daily": "https://meta.icos-cp.eu/collections/_l85vWiIV81AifoxCkty50YI",
                "005_monthly": "https://meta.icos-cp.eu/collections/_l85vWiIV81AifoxCkty50YI",
            }
        ),
        "FLUXCOM-X-BASE_ET_T": FluxcomDataset(
            agg_mode={
                "005_hourly": "https://swift.dkrz.de/v1/dkrz_a1e106384d7946408b9724b59858a536/fluxcom-x/FLUXCOMxBase/ET_T",
                "050_monthly": "https://meta.icos-cp.eu/collections/aCBG-AZIJtCCia7bhMYWin1-",
                "025_monthlycycle": "https://meta.icos-cp.eu/collections/aCBG-AZIJtCCia7bhMYWin1-",
                "025_daily": "https://meta.icos-cp.eu/collections/aCBG-AZIJtCCia7bhMYWin1-",
                "005_monthly": "https://meta.icos-cp.eu/collections/aCBG-AZIJtCCia7bhMYWin1-",
            }
        ),
    }


SELECTION_PARAMS = dict(
    agg_mode=JsonStringSchema(
        title="Aggregation mode",
        description="Note that '005_hourly' is the non-aggregated dataset.",
        enum=[
            "005_hourly",
            "050_monthly",
            "025_monthlycycle",
            "025_daily",
            "005_monthly",
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
