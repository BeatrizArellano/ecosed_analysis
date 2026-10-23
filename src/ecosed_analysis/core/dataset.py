"""Minimal dataset inspection, performed once when needed."""
from dataclasses import dataclass
import xarray as xr
from .geometry import sediment_mask


@dataclass(frozen=True)
class DatasetInfo:
    has_sediments: bool
    water_layers: int
    sediment_layers: int
    available_variables: tuple[str, ...]


def inspect_dataset(ds: xr.Dataset) -> DatasetInfo:
    sed = sediment_mask(ds)
    nsed = int(sed.sum())
    return DatasetInfo(
        has_sediments=nsed > 0,
        water_layers=ds.sizes["depth"] - nsed,
        sediment_layers=nsed,
        available_variables=tuple(ds.data_vars),
    )
