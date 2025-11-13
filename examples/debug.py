from xcube.core.store import new_data_store

store = new_data_store("icosdp")
ds = store.open_data(
    data_id="FLUXCOM-X-BASE_NEE",
    time_range=("2020-01-01", "2021-12-31"),
    bbox=[5, 45, 10, 50],  # lon_min, lat_min, lon_max, lat_max
    flatten_time=True,
)
print(ds)
