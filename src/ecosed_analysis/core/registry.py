"""Known model names and scientific metadata. Add new modules incrementally."""
from dataclasses import dataclass


@dataclass(frozen=True)
class VariableSpec:
    name: str
    aliases: tuple[str, ...] = ()
    sediment_phase: str | None = None  # solid, porewater, or None
    label: str | None = None
    units: str | None = None
    quantity: str | None = None
    kind: str = "state"


SPECS = {
    "phytoplankton": VariableSpec("phy_biomass", ("pelagic_phy",), label="Phytoplankton"),
    "zooplankton": VariableSpec("zoo_biomass", ("pelagic_zoo",), label="Zooplankton"),
    "nitrate": VariableSpec("nitrogen_no3", sediment_phase="porewater", label="Nitrate"),
    "ammonium": VariableSpec("nitrogen_nh4", sediment_phase="porewater", label="Ammonium"),
    "oxygen": VariableSpec("oxygen_o2", sediment_phase="porewater", label="Oxygen"),
    "sulfate": VariableSpec("sulfur_so4", sediment_phase="porewater", label="Sulfate"),
    "sulfide": VariableSpec("sulfur_sulfide", sediment_phase="porewater", label="Sulfide"),
    "pom_labile": VariableSpec("remin_pom_l", sediment_phase="solid", label="Labile POM"),
    "pom_semilabile": VariableSpec("remin_pom_s", sediment_phase="solid", label="Semi-labile POM"),
    "pom_refractory": VariableSpec("remin_pom_r", sediment_phase="solid", label="Refractory POM"),
    "primary_production": VariableSpec("phy_TPP", ("pelagic_TPP",), label="Primary production"),
    "chlorophyll": VariableSpec("total_chlorophyll", ("pelagic_chl",), label="Chlorophyll"),
    "temperature": VariableSpec("temperature", label="Temperature"),
}



# Reaction diagnostics from the default 'remin' and 'pyrite' module instances.
# The instance prefix is essential: PYRITE_FORM is on different volume bases
# in these two modules. Values in the sediment are converted to area rates
# with (1 - porosity) * dz for solids and porosity * dz for porewater.
_REMIN_SOLID = (
    "REM", "REM_AER", "REM_DENIT", "REM_MN", "REM_FE",
    "REM_SO4", "REM_CH4",
)
_REMIN_POREWATER = ("NLOSS_DENIT",)
_REMIN_ALK = (
    "ALK_PROD_PYRITE", "ALK_PROD_AER", "ALK_PROD_DENIT",
    "ALK_PROD_MN", "ALK_PROD_FE", "ALK_PROD_SO4",
    "ALK_PROD_CH4", "ALK_PROD_REM",
)

for _suffix in _REMIN_SOLID:
    SPECS[f"remin_{_suffix}"] = VariableSpec(
        name=f"remin_{_suffix}", sediment_phase="solid",
        units="mmol N m-3 d-1", quantity="N", kind="rate",
    )
for _suffix in _REMIN_POREWATER:
    SPECS[f"remin_{_suffix}"] = VariableSpec(
        name=f"remin_{_suffix}", sediment_phase="porewater",
        units="mmol N m-3 d-1", quantity="N", kind="rate",
    )
for _suffix in _REMIN_ALK:
    SPECS[f"remin_{_suffix}"] = VariableSpec(
        name=f"remin_{_suffix}", sediment_phase="porewater",
        units="mmol eq m-3 d-1", quantity="alkalinity", kind="rate",
    )
# This diagnostic originates from organic-matter degradation, on the solid
# volume basis. It is distinct from the Fe-dependent pyrite module diagnostic.
SPECS["remin_PYRITE_FORM"] = VariableSpec(
    name="remin_PYRITE_FORM", sediment_phase="solid",
    units="mmol m-3 d-1", quantity="pyrite", kind="rate",
)
for _suffix, _phase, _units, _quantity in (
    ("PYRITE_FORM", "porewater", "mmol m-3 d-1", "pyrite"),
    ("PYRITE_OX_O2", "solid", "mmol m-3 d-1", "pyrite"),
    ("ALK_PYRITE_FORM", "porewater", "mmol eq m-3 d-1", "alkalinity"),
    ("ALK_PYRITE_OX", "porewater", "mmol eq m-3 d-1", "alkalinity"),
):
    SPECS[f"pyrite_{_suffix}"] = VariableSpec(
        name=f"pyrite_{_suffix}", sediment_phase=_phase,
        units=_units, quantity=_quantity, kind="rate",
    )

def resolve_variable(ds, name: str) -> str:
    """Find an exact NetCDF name, or the single available alias for a canonical name.

    Prefers explicit dataset variable names. Ambiguous aliases raise an error.
    """
    if name in ds:
        return name
    if name not in SPECS:
        raise KeyError(f"Unknown variable {name!r}; pass an existing NetCDF name or register it.")
    spec = SPECS[name]
    matches = [candidate for candidate in (spec.name, *spec.aliases) if candidate in ds]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one variable for {name!r}, found {matches}.")
    return matches[0]


def sediment_phase(name: str) -> str | None:
    """Return registered phase for a canonical name or a NetCDF alias."""
    for key, spec in SPECS.items():
        if name == key or name in (spec.name, *spec.aliases):
            return spec.sediment_phase
    return None
