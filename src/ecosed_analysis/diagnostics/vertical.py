"""Centre-defined vertical integration; calculations are independent of plots."""
import numpy as np
import xarray as xr
from ecosed_analysis.core import integration_weights, resolve_variable, sediment_phase


def vertical_integral(ds: xr.Dataset, variable: str, *, domain: str = "water", phase: str | None = None) -> xr.DataArray:
    """Integrate a volumetric concentration or rate over water or sediment.

    Sediment phase is required, either explicitly or from the registry. Results
    retain non-vertical dimensions such as time. Caller must verify units and
    distinguish annual mean rates from cumulative annual production.
    """
    actual = resolve_variable(ds, variable)
    da = ds[actual]
    if "depth" not in da.dims or "depth_interface" in da.dims:
        raise ValueError(f"{actual!r} must be defined at depth cell centres.")
    if domain == "sediment" and phase is None:
        phase = sediment_phase(variable)
    weights = integration_weights(ds, domain=domain, phase=phase)
    selected = weights > 0
    if not bool(selected.any()):
        raise ValueError("No positive integration weights in the requested domain.")
    if bool((~xr.apply_ufunc(np.isfinite, da)).where(selected, False).any()):
        raise ValueError(f"Non-finite {actual!r} values in the requested domain.")
    result = (da.where(selected, 0) * weights).sum("depth", min_count=1)
    result.name = f"{actual}_{domain}_integral"
    result.attrs = {"long_name": f"Vertically integrated {da.attrs.get('long_name', actual)}", "source_variable": actual, "domain": domain, "phase": phase if domain == "sediment" else "water", "integration_method": "thickness_weighted"}
    units = da.attrs.get("units", "")
    if units:
        result.attrs["source_units"] = units
        result.attrs["units"] = units.replace("m-3", "m-2") if "m-3" in units else f"({units}) m"
    return result
