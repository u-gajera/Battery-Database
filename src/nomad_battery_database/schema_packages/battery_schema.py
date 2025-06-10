
from __future__ import annotations

import ast
from numbers import Number
from typing import TYPE_CHECKING, Any

import numpy as np
from nomad.datamodel.data import Schema
from nomad.datamodel.metainfo.annotations import ELNAnnotation, ELNComponentEnum
from nomad.datamodel.metainfo.basesections import ElementalComposition
from nomad.datamodel.results import Material, Results
from nomad.metainfo import Quantity, SchemaPackage, Section, SubSection

if TYPE_CHECKING:  
    from nomad.datamodel import EntryArchive
    from structlog.stdlib import BoundLogger

m_package = SchemaPackage()

#  Helper utilities
def _parse_composition(
        raw: str | list | None
    ) -> tuple[list[str], list[float]] | None:

    if raw is None:
        return None
    if isinstance(raw, str):
        try:
            parts = ast.literal_eval(raw)
        except Exception:
            return None
    elif isinstance(raw, list):
        parts = raw
    else:
        return None
    if not all(isinstance(p, dict) for p in parts):
        return None
    totals: dict[str, float] = {}
    for part in parts:
        for el, cnt in part.items():
            totals[el] = totals.get(el, 0.0) + float(cnt or 1.0)
    elems = sorted(totals)
    if "C" in elems:
        elems.remove("C")
        elems.insert(0, "C")

    if "H" in elems:
        elems.remove("H")
        insert_pos = 1 if elems[0] == "C" else 0
        elems.insert(insert_pos, "H")


def _to_number(val: Any) -> float | None:  
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None
    if hasattr(val, "magnitude"):
        try:
            return float(val.to_base_units().magnitude)  
        except Exception:
            return float(val.magnitude)  
    if isinstance(val, Number):
        return float(val)
    return None

# -----------------------------------------------------------------------------
#  Sub‑sections for Results.properties #needed to create
# class BatterySummary(Schema):
#     m_def = Section(label="Battery summary (curated DB)")
#     capacity             = Quantity(type=np.float64, unit="mA*hour/g")
#     voltage              = Quantity(type=np.float64, unit="V")
#     coulombic_efficiency = Quantity(type=np.float64)
#     energy_density       = Quantity(type=np.float64, unit="W*hour/kg")
#     conductivity         = Quantity(type=np.float64, unit="S/cm")

# class ElectrochemistryProps(Schema):
#     m_def = Section(label="Electrochemistry properties")
#     battery = SubSection(sub_section=BatterySummary)

# # Attach our new subsection definition to the *standard* Properties section
# if not hasattr(Properties, "electrochemistry"):
#     Properties.electrochemistry = SubSection(section_def=ElectrochemistryProps)

# -----------------------------------------------------------------------------
#  BatteryProperties (material‑level section)
class BatteryProperties(Schema):
    """Metadata for one material extracted from the curated battery DB."""

    # bibliographic ------------------------------------------------------
    material_name = Quantity(type=str, 
                    a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity))
    extracted_name = Quantity(type=str)
    chemical_formula_hill = Quantity(type=str)
    elements = Quantity(type=str, shape=["*"])
    title = Quantity(type=str)
    DOI = Quantity(type=str)
    journal = Quantity(type=str)
    date = Quantity(type=str)

    # meta ---------------------------------------------------------------
    specifier = Quantity(type=str)
    tag = Quantity(type=str)
    warning = Quantity(type=str)
    correctness = Quantity(type=str)
    material_type = Quantity(type=str)
    info = Quantity(type=str)

    # raw numerical ------------------------------------------------------
    capacity_raw_value = Quantity(type=np.float64)
    capacity_raw_unit  = Quantity(type=str)
    voltage_raw_value  = Quantity(type=np.float64)
    voltage_raw_unit   = Quantity(type=str)
    coulombic_efficiency_raw_value = Quantity(type=np.float64)
    coulombic_efficiency_raw_unit  = Quantity(type=str)
    energy_density_raw_value = Quantity(type=np.float64)
    energy_density_raw_unit  = Quantity(type=str)
    conductivity_raw_value   = Quantity(type=np.float64)
    conductivity_raw_unit    = Quantity(type=str)

    # normalised numbers -------------------------------------------------
    capacity             = Quantity(type=np.float64, unit="mA*hour/g")
    voltage              = Quantity(type=np.float64, unit="V")
    coulombic_efficiency = Quantity(type=np.float64)
    energy_density       = Quantity(type=np.float64, unit="W*hour/kg")
    conductivity         = Quantity(type=np.float64, unit="S/cm")

    # ------------------------------------------------------------------
    #  Normaliser
    def normalize(self, archive: EntryArchive, logger: BoundLogger) -> None:  
        super().normalize(archive, logger)

        # 1) composition & results.material -----------------------------
        EPSILON = 1e-6
        comp = _parse_composition(self.extracted_name)
        if comp is not None:
            elements, counts = comp
            self.elements = elements

            if not self.chemical_formula_hill:
                self.chemical_formula_hill = "".join(
                    el if abs(cnt - 1.0) < EPSILON else (
                        f"{el}{int(cnt) if float(cnt).is_integer() else cnt}"
                    )
                    for el, cnt in zip(elements, counts)
                )
            if archive.results is None:
                archive.results = Results()  
            mat: Material = getattr(archive.results, "material", None) or Material()
            archive.results.material = mat  
            total = float(sum(counts))
            mat.chemical_formula_hill = self.chemical_formula_hill
            mat.elements = elements  
            mat.nelements = len(elements)  
            mat.elements_ratios = [c / total for c in counts]  
            archive.results.elemental_composition = [
                ElementalComposition(element=el, atomic_fraction=cnt / total)
                for el, cnt in zip(elements, counts)
            ]  

        # 2) map *_raw_value → clean fields -----------------------------
        for raw, clean in [
            ("capacity_raw_value", "capacity"),
            ("voltage_raw_value", "voltage"),
            ("coulombic_efficiency_raw_value", "coulombic_efficiency"),
            ("energy_density_raw_value", "energy_density"),
            ("conductivity_raw_value", "conductivity"),
        ]:
            val = getattr(self, raw, None)
            if val is not None and not np.isnan(val):
                setattr(self, clean, val)

        # 3) custom units (optional) -----------------------------------
        for raw_u, clean in [
            ("capacity_raw_unit", "capacity"),
            ("voltage_raw_unit", "voltage"),
            ("energy_density_raw_unit", "energy_density"),
            ("conductivity_raw_unit", "conductivity"),
        ]:
            unit = getattr(self, raw_u, None)
            if unit and getattr(self, clean, None) is not None:
                try:
                    getattr(self, clean).unit = unit  
                except Exception:
                    pass

        # 4) populating results.properties.electrochemistry.battery ------
        # if archive.results is None:
        #     archive.results = Results()  
        # props_sec: Properties = getattr(archive.results, "properties", None)  
        # if props_sec is None:
        #     props_sec = archive.results.m_create(Properties) 
        # elec_sec: ElectrochemistryProps = getattr(props_sec, 
        #                                           "electrochemistry", 
        #                                           None)  
        # if elec_sec is None:
        #     elec_sec = props_sec.m_create(ElectrochemistryProps) 
        #     props_sec.electrochemistry = elec_sec  # attach
        # batt: BatterySummary = getattr(elec_sec, "battery", None)  
        # if batt is None:
        #     batt = elec_sec.m_create(BatterySummary)
        #     elec_sec.battery = batt
        # for key in [
        #     "capacity",
        #     "voltage",
        #     "coulombic_efficiency",
        #     "energy_density",
        #     "conductivity",
        # ]:
        #     num = _to_number(getattr(self, key, None))
        #     if num is not None:
        #         setattr(batt, key, num)

# -----------------------------------------------------------------------------
#  Top‑level container
class BatteryDatabase(Schema):
    m_def = Section(label="Battery database", 
                    extends=["nomad.datamodel.data.EntryData"])
    Material_entries = SubSection(sub_section=BatteryProperties, 
                                  repeats=True)

m_package.__init_metainfo__()

__all__ = ["m_package", 
           "BatteryProperties", 
           "BatteryDatabase"]