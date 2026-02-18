## Changes in 0.1.1

- Skip requests for datasets that are already preloaded to avoid redundant processing.
- Ensure consistent chunk sizes for preloaded datasets.
  Default chunking is now `(1, 1800, 1800)` for `(time, lat, lon)`.


## Changes in 0.1.0

- Initial release of `xcube-icosdp`.
- Added a data store to access **FLUXCOM-X-BASE** products
- Access the native full resolution dataset (0.05° spatial, hourly temporal,
  2001-2021) via `open_data` method
- Access the aggregated methods pubsihed at https://meta.icos-cp.eu/collections/zfwf1Ak2I7OlziGDTX8Xl6_T
  via `preload_data` method

