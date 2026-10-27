"""Known model names and scientific metadata. Add new modules incrementally."""
from dataclasses import dataclass


@dataclass(frozen=True)
class VariableSpec:
    name: str
    aliases: tuple[str, ...] = ()
    sediment_phase: str | None = None  # solid, porewater, or None
    label: str | None = None


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
