# xcube-icosdp

[![Build Status](https://github.com/xcube-dev/xcube-icosdp/actions/workflows/unit-tests.yml/badge.svg?branch=main)](https://github.com/xcube-dev/xcube-icosdp/actions/workflows/unit-tests.yml)
[![codecov](https://codecov.io/gh/xcube-dev/xcube-icosdp/graph/badge.svg?token=ktcp1maEgz)](https://codecov.io/gh/xcube-dev/xcube-icosdp)
[![PyPI Version](https://img.shields.io/pypi/v/xcube-icosdp)](https://pypi.org/project/xcube-icosdp/)
[![Anaconda-Server Badge](https://anaconda.org/conda-forge/xcube-icosdp/badges/version.svg)](https://anaconda.org/conda-forge/xcube-icosdp)
[![Anaconda-Server Badge](https://anaconda.org/conda-forge/xcube-icosdp/badges/license.svg)](https://anaconda.org/conda-forge/xcube-icosdp)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

`xcube-icosdp` is a Python package and [xcube plugin](https://xcube.readthedocs.io/en/latest/plugins.html)
that provides a [data store](https://xcube.readthedocs.io/en/latest/api.html#data-store-framework) for accessing data from the
[ICOS Data Portal](https://data.icos-cp.eu/portal/).

---

## Supported Datasets

The plugin currently supports the **FLUXCOM-X-BASE** products for carbon and water fluxes.
For details on FLUXCOM-X-BASE data products, see:

> Nelson and Walther et al. (2024): https://doi.org/10.5194/egusphere-2024-165

X-BASE contains four flux variables:

- **NEE** — Net Ecosystem Exchange
- **GPP** — Gross Primary Productivity
- **ET** — Evapotranspiration
- **ET_T** — Transpiration

To improve usability, the data is available through:

✅ Native resolution via cloud-optimized access (spatial/temporal subsetting)
✅ Pre-computed spatial & temporal aggregations


### Native Full-Resolution Dataset

- **005_hourly** — 0.05° spatial and hourly temporal resolution for 2001–2021 (~3 TB)

Each dataset has dimensions `(time, hour, lat, lon)` and includes a `land_fraction` variable.

The data is stored in **Zarr** format on a publicly accessible object storage hosted by
[DKRZ](https://www.dkrz.de/en/dkrz-partner-for-climate-research?set_language=en).
It is **cloud-optimized**, allowing efficient spatial and temporal subsetting.
No authentication is required to access the dataset.


### Aggregated Products

All aggregated datasets are distributed through the
[ICOS ERIC Carbon Portal](https://meta.icos-cp.eu/collections/zfwf1Ak2I7OlziGDTX8Xl6_T)
(CC BY-4.0 license) in NetCDF format.

Current aggregations:

| Dataset              | Spatial Resolution | Temporal Resolution        | Size per Year | Dimensions |
|----------------------|--------------------|----------------------------|---------------|------------|
| **050_monthly**      | 0.5°               | Monthly                    | ~5 MB         |`(time, lat, lon)`|
| **025_monthlycycle** | 0.25°              | Monthly mean diurnal cycle | ~270 MB       |`(time, hour, lat, lon)`|
| **025_daily**        | 0.25°              | Daily                      | ~380 MB       |`(time, lat, lon)`|
| **005_monthly**      | 0.05°              | Monthly                    | ~450 MB       |`(time, lat, lon)`|

All files include `land_fraction`.

---

## Using the `xcube-icosdp` Data Store

Example: open the **NEE** flux for 2020–2021 over a custom bounding box:

```python
from xcube.core.store import new_data_store

store = new_data_store("icosdp")
ds = store.open_data(
    data_id="NEE",
    time_range=("2020-01-01", "2021-12-31"),
    bbox=[5, 45, 10, 50]  # lon_min, lat_min, lon_max, lat_max
)
```

🌐 Public data — no authentication required at this time.
📖 [Example notebook](examples/access_fluxcomxbase.ipynb)

> 💡 Note: Authentication-based access for aggregated ICOS datasets will be supported
> in a future release. Additional workflows will be documented in new example notebooks.

## Installing the xcube-icosdp plugin

This section describes three alternative methods you can use to install the
xcube-icosdp plugin.

For installation of conda packages, we recommend
[mamba](https://mamba.readthedocs.io/). It is also possible to use conda,
but note that installation may be significantly slower with conda than with
mamba. If using conda rather than mamba, replace the `mamba` command with
`conda` in the installation commands given below.

### Installation into a new environment with mamba

This method creates a new environment and installs the latest conda-forge
release of xcube-icosdp, along with all its required dependencies, into the
newly created environment.

To do so, execute the following commands:

```bash
mamba create --name xcube-icosdp --channel conda-forge xcube-icosdp
mamba activate xcube-icosdp
```

The name of the environment may be freely chosen.

### Installation into an existing environment with mamba

This method assumes that you have an existing environment, and you want
to install xcube-icosdp into it.

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