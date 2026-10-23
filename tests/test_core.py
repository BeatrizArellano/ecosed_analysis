import numpy as np
import pytest
import xarray as xr

from ecosed_analysis.core import inspect_dataset, swi_depth, resolve_variable
from ecosed_analysis.diagnostics import vertical_integral


def example(coupled=True):
    coords = {"depth": [1.0, 3.0, 4.0005], "depth_interface": [0.0, 2.0, 4.0, 4.001]}
    if not coupled:
        coords = {"depth": [1.0, 3.0], "depth_interface": [0.0, 2.0, 4.0]}
    n = len(coords["depth"])
    ds = xr.Dataset({"dz": ("depth", [2.0, 2.0] + ([0.001] if coupled else [])),
                     "nitrogen_no3": ("depth", np.full(n, 10.0)),
                     "remin_pom_r": ("depth", np.full(n, 100.0))}, coords=coords)
    if coupled:
        ds["sediment_mask"] = ("depth", [0, 0, 1])
        ds["porosity"] = ("depth", [1.0, 1.0, 0.8])
    return ds


def test_water_only():
    ds = example(False)
    assert not inspect_dataset(ds).has_sediments
    assert float(vertical_integral(ds, "nitrate")) == 40
    with pytest.raises(ValueError, match="No sediment"):
        vertical_integral(ds, "nitrate", domain="sediment")


def test_coupled():
    ds = example()
    assert inspect_dataset(ds).sediment_layers == 1
    assert swi_depth(ds) == 4.0
    assert np.isclose(float(vertical_integral(ds, "nitrate", domain="sediment")), 0.008)
    assert np.isclose(float(vertical_integral(ds, "pom_refractory", domain="sediment")), 0.02)


def test_ambiguous_and_interface():
    ds = example()
    ds["Kz"] = ("depth_interface", np.ones(4))
    with pytest.raises(ValueError, match="cell centres"):
        vertical_integral(ds, "Kz")
    ds2 = example(False)
    ds2["porosity"] = ("depth", [1.0, 1.0])
    with pytest.raises(ValueError, match="sediment_mask"):
        inspect_dataset(ds2)


def test_alias():
    ds = example(False).rename({"nitrogen_no3": "old_no3"})
    with pytest.raises(ValueError, match="Expected exactly one"):
        resolve_variable(ds, "nitrate")
