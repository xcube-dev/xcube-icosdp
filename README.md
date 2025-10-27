# xcube-icosdp

[![Build Status](https://github.com/xcube-dev/xcube-icosdp/actions/workflows/unit-tests.yml/badge.svg?branch=main)](https://github.com/xcube-dev/xcube-icosdp/actions/workflows/unit-tests.yml)
[![codecov](https://codecov.io/gh/xcube-dev/xcube-icosdp/graph/badge.svg?token=ktcp1maEgz)](https://codecov.io/gh/xcube-dev/xcube-icosdp)
[![PyPI Version](https://img.shields.io/pypi/v/xcube-icosdp)](https://pypi.org/project/xcube-icosdp/)
[![Anaconda-Server Badge](https://anaconda.org/conda-forge/xcube-icosdp/badges/version.svg)](https://anaconda.org/conda-forge/xcube-icosdp)
[![Anaconda-Server Badge](https://anaconda.org/conda-forge/xcube-icosdp/badges/license.svg)](https://anaconda.org/conda-forge/xcube-icosdp)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

`xcube-icosdp` is a Python package and a [xcube plugin](https://xcube.readthedocs.io/en/latest/plugins.html)
that provides a [data store](https://xcube.readthedocs.io/en/latest/api.html#data-store-framework)
for accessing data from the [ICOS Data Portal](https://data.icos-cp.eu/portal/).


## What datasets are supported

the FLUXCOM-X-BASE products of carbon and water fluxes.
For a detailed overview of the FLUXCOM-X framework and the X-BASE data products,
please refer to the associated paper:
[Nelson and Walther et al. 2024](https://doi.org/10.5194/egusphere-2024-165)

The X-BASE data products contain four fluxes:

- **NEE:** Net Ecosystem Exchange
- **GPP:** Gross Primary Productivity
- **ET:** Evapotranspiration
- **ET_T:** Transpiration

Each flux has a native resolution of 0.05° spatially and hourly, resulting in large outputs (~3 TB).
In order to make this data more managable for users,
we have a number of access options,
including cloud optimized formats for subsetting,
as well as spatial and temporal aggregates.

### Full Resolution Dataset

- **005_hourly:** 0.05° spatial and hourly temporal resolution (~3 TB for 21 Years)

2001-2021
While the aggregated products distributed through the Carbon Portal will suit many use cases,
there might be applications that need access to the full resolution (0.05 degree, hourly) dataset.
The data is stored in the zarr format and in a publicly available object store provided by [DKRZ](https://www.dkrz.de/en/dkrz-partner-for-climate-research?set_language=en).


### Spatial/Temporal Aggregates

All aggregated products are available via the [ICOS ERIC Carbon Portal](https://meta.icos-cp.eu/collections/zfwf1Ak2I7OlziGDTX8Xl6_T)
with a CCBY4 Data Licence in NetCDF files. There are four pre-computed aggregations currently available:

- **050_monthly:** 0.5° spatial and monthly temporal aggregation (~5 MB per year)
- **025_monthlycycle:** 0.25° spatial with the monthly mean diurnal cycle (~270 MB per year)
- **025_daily:** 0.25° spatial and daily temporal aggregation (~380 MB per year)
- **005_monthly:** 0.05° spatial and monthly temporal aggregation (~450 MB per year)

Each file has the flux values in the dimension of `(time, lat, lon)` or `(time, hour, lat, lon)`
for in the case of the *025_monthlycycle*.
Each file also contains the associated land area fraction (`land_fraction`).
Below find the links to each individual files.


## How to use the xcube-icosdp plugin

To access X-BASE data products in full resolution use the following code snippet which initiate a xcube
data store and access the full resolution dataset by default.

```python
from xcube.core.store import new_data_store

store = new_data_store("icosdp")
ds = store.open_data(
    "NEE",
    time_range=("2020-01-01", "2021-12-31"),
    bbox=[5, 45, 10, 50]
)
```

Note that the full resolution datasets are available via a public object storeage, and thus
no authentification is needed. AN example note book shows further funtionalities of the
data store [Example Notebook](examples/access_fluxcomxbase.ipynb)

> Note the following in in planning and comes in the future.
for the aggregated datasets the data access via ICOS Data Potal inlcuding auhtentifciation will be described here.
To learn more check out the Example note books:

## Installing the xcube-icosdp plugin

This section describes three alternative methods you can use to install the
xcube-zenodo plugin.

> Note the publication of conda will come in the near future.

For installation of conda packages, we recommend
[mamba](https://mamba.readthedocs.io/). It is also possible to use conda,
but note that installation may be significantly slower with conda than with
mamba. If using conda rather than mamba, replace the `mamba` command with
`conda` in the installation commands given below.

### Installation into a new environment with mamba

This method creates a new environment and installs the latest conda-forge
release of xcube-zenodo, along with all its required dependencies, into the
newly created environment.

To do so, execute the following commands:

```bash
mamba create --name xcube-icosdp --channel conda-forge xcube-icosdp
mamba activate xcube-icosdp
```

The name of the environment may be freely chosen.

### Installation into an existing environment with mamba

This method assumes that you have an existing environment, and you want
to install xcube-zenodo into it.

With the existing environment activated, execute this command:

```bash
mamba install --channel conda-forge xcube-icosdp
```

Once again, xcube and any other necessary dependencies will be installed
automatically if they are not already installed.

> Note till here will come soon

### Installation into an existing environment from the repository

If you want to install xcube-icosdp directly from the git repository (for example
in order to use an unreleased version or to modify the code), you can
do so as follows:

```bash
mamba create --name xcube-icosdp --channel conda-forge --only-deps xcube-icosdp
mamba activate xcube-icosdp
git clone https://github.com/xcube-dev/xcube-icosdp.git
python -m pip install --no-deps --editable xcube-icosdp/
```

This installs all the dependencies of xcube-icosdp into a fresh conda environment,
then installs xcube-icosdp into this environment from the repository.

## Testing <a name="testing"></a>

To run the unit test suite:

```bash
pytest
```

To analyze test coverage:

```bash
pytest --cov=xcube_icosdp
```

To produce an HTML
[coverage report](https://pytest-cov.readthedocs.io/en/latest/reporting.html):

```bash
pytest --cov-report html --cov=xcube_icosdp
```