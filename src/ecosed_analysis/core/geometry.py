"""Model-aware vertical geometry. No hard-coded model depths."""
import numpy as np
import xarray as xr


def water_mask(ds: xr.Dataset) -> xr.DataArray:
    """Boolean mask at cell centres; absent sediment_mask implies water-only."""
    if "depth" not in ds.dims:
        raise ValueError("Dataset must have 'depth' dimension.")
    if "sediment_mask" not in ds:
        if any(v in ds for v in ("porosity", "tortuosity2", "bioirrigation", "bioturbation")):
            raise ValueError("Sediment geometry detected but sediment_mask is absent.")
        return xr.ones_like(ds["depth"], dtype=bool)
    mask = ds["sediment_mask"]
    if mask.dims != ("depth",):
        raise ValueError("sediment_mask must have dimension ('depth',).")
    if not bool(((mask == 0) | (mask == 1)).all()):
        raise ValueError("sediment_mask must contain only 0 (water) and 1 (sediment).")
    return mask == 0


def sediment_mask(ds: xr.Dataset) -> xr.DataArray:
    """Boolean sediment cell mask."""
    return ~water_mask(ds)


def swi_depth(ds: xr.Dataset) -> float:
    """SWI depth in metres from the upper interface of the first sediment cell."""
    sed = sediment_mask(ds).values
    if not sed.any():
        raise ValueError("No sediment cells exist.")
    i = int(np.flatnonzero(sed)[0])
    if not np.all(sed[i:]) or np.any(sed[:i]):
        raise ValueError("Sediment layers must form a single contiguous lower block.")
    if "depth_interface" not in ds.coords or ds.sizes["depth_interface"] != ds.sizes["depth"] + 1:
        raise ValueError("Expected depth_interface to have one more element than depth.")
    return float(ds["depth_interface"].isel(depth_interface=i))


def sediment_depth_cm(ds: xr.Dataset) -> xr.DataArray:
    """Cell-centre depth below SWI (negative values occur in water)."""
    return (ds["depth"] - swi_depth(ds)) * 100.0


def integration_weights(ds: xr.Dataset, domain: str = "water", phase: str | None = None) -> xr.DataArray:
    """Equivalent bulk thickness in metres for a centre-defined concentration."""
    if "dz" not in ds or ds["dz"].dims != ("depth",):
        raise ValueError("dz(depth) is required.")
    if bool((~np.isfinite(ds["dz"])).any()) or bool((ds["dz"] <= 0).any()):
        raise ValueError("dz must be finite and positive.")
    if domain == "water":
        if phase not in (None, "water"):
            raise ValueError("Water integration does not use sediment phases.")
        return ds["dz"].where(water_mask(ds), 0)
    if domain != "sediment":
        raise ValueError("domain must be 'water' or 'sediment'.")
    if not bool(sediment_mask(ds).any()):
        raise ValueError("No sediment cells exist.")
    if phase not in ("solid", "porewater", "bulk"):
        raise ValueError("Sediment phase must be explicitly 'solid', 'porewater', or 'bulk'.")
    factor = 1.0
    if phase != "bulk":
        if "porosity" not in ds or ds["porosity"].dims != ("depth",):
            raise ValueError("Sediment solid/porewater integration requires porosity(depth).")
        phi = ds["porosity"].where(sediment_mask(ds), 0)
        if bool(((phi < 0) | (phi > 1)).any()):
            raise ValueError("Porosity must be between 0 and 1.")
        factor = phi if phase == "porewater" else 1 - phi
    return (ds["dz"] * factor).where(sediment_mask(ds), 0)
