from xcube.core.store import new_data_store

store = new_data_store(
    "icosdp",
    email="konstantin.ntokas@brockmann-consult.de",
    password="t5qm~hci|]itk"
)

cache_store = store.preload_data(
    "FLUXCOM-X-BASE_NEE",
    agg_mode="050_monthly",
    time_range=("2020-01-01", "2021-12-31"),
    bbox=[5, 45, 10, 50]
)
data_ids = cache_store.list_data_ids()
print(data_ids)
ds = cache_store.open_data(data_ids[0])
print(ds)