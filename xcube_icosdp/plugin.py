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

from xcube.constants import EXTENSION_POINT_DATA_STORES
from xcube.util import extension

from .constants import DATA_STORE_ID


def init_plugin(ext_registry: extension.ExtensionRegistry):
    ext_registry.add_extension(
        loader=extension.import_component("xcube_icosdp.store:IcosdpDataStore"),
        point=EXTENSION_POINT_DATA_STORES,
        name=DATA_STORE_ID,
        description="ICOS Data Portal Data Store",
    )
