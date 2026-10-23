# ecosed_analysis

Reusable, configuration-aware analysis utilities for pelagic and coupled sediment models.

## Install

```bash
pip install -e ".[dev]"
pytest
```

## Example

```python
import xarray as xr
from ecosed_analysis.core import inspect_dataset, water_mask, sediment_mask
from ecosed_analysis.diagnostics import vertical_integral

ds = xr.open_dataset("simulation.nc")
print(inspect_dataset(ds))
water_no3 = vertical_integral(ds, "nitrogen_no3", domain="water")
# Sediment POM concentrations are per solid volume; use phase="solid".
if inspect_dataset(ds).has_sediments:
    sediment_pom = vertical_integral(ds, "remin_pom_r", domain="sediment", phase="solid")
```

## Principles

- `sediment_mask` (0 water, 1 sediment) is authoritative when present; without it, geometry is treated as water-only unless sediment geometry indicators make the dataset ambiguous.
- `dz` contains layer thicknesses in metres.
- Concentrations and rates are at `depth` centres; interface fields such as mixing/velocity belong at `depth_interface` and cannot be directly integrated as concentrations.
- Sediment dissolved concentrations are per porewater volume; solids per solid volume.
- A registry provides known scientific metadata. Unknown variables remain available through xarray and generic plotting.
- Missing optional variables should not be fabricated or silently replaced by zero.

Validation, specialised plotting, and experiment orchestration modules are intentionally placeholders for subsequent milestones.
