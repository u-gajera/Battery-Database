
from __future__ import annotations

import ast
from numbers import Number
from typing import TYPE_CHECKING, Any, Optional

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
def _parse_composition(raw: str | list | None) -> Optional[tuple[list[str], 
                                                                 list[float]]]:
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
        elems.remove("C"); elems.insert(0, "C")
    if "H" in elems:
        elems.remove("H"); elems.insert(1 if elems[0] == "C" else 0, "H")
    counts = [totals[e] for e in elems]
    return elems, counts


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

class BatteryProperties(Schema):

    material_name        = Quantity(type=str, 
                a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity))
    extracted_name       = Quantity(type=str)
    chemical_formula_hill = Quantity(type=str)
    elements             = Quantity(type=str, shape=["*"])
    title                = Quantity(type=str)
    DOI                  = Quantity(type=str)
    journal              = Quantity(type=str)
    date                 = Quantity(type=str)

    specifier          = Quantity(type=str)
    tag                = Quantity(type=str)
    warning            = Quantity(type=str)
    correctness        = Quantity(type=str)
    info               = Quantity(type=str)
    capacity_raw_value = Quantity(type=np.float64)
    capacity_raw_unit  = Quantity(type=str)
    voltage_raw_value  = Quantity(type=np.float64)
    voltage_raw_unit   = Quantity(type=str)
    coulombic_efficiency_raw_value = Quantity(type=np.float64)
    coulombic_efficiency_raw_unit  = Quantity(type=str)
    energy_density_raw_value       = Quantity(type=np.float64)
    energy_density_raw_unit        = Quantity(type=str)
    conductivity_raw_value         = Quantity(type=np.float64)
    conductivity_raw_unit          = Quantity(type=str)

    capacity             = Quantity(type=np.float64, unit="mA*hour/g")
    voltage              = Quantity(type=np.float64, unit="V")
    coulombic_efficiency = Quantity(type=np.float64)
    energy_density       = Quantity(type=np.float64, unit="W*hour/kg")
    conductivity         = Quantity(type=np.float64, unit="S/cm")

    # properties_included = Quantity(type=str,shape=["*"],                 
    #             description="Names of measured properties that are present "
    #                         "for this entry.",
    #         )
    #  Normaliser
    def normalize(self, archive: EntryArchive, logger: BoundLogger) -> None:  
        super().normalize(archive, logger)

        comp = _parse_composition(self.extracted_name)
        if comp is not None:
            elements, counts = comp
            self.elements = elements
            if not self.chemical_formula_hill:
                self.chemical_formula_hill = "".join(
                    el if abs(cnt - 1.0) < 1e-6 else f"{el}{int(cnt) if float(cnt).is_integer() else cnt}"
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

        for raw, clean in [
            ("capacity_raw_value", "capacity"),
            ("voltage_raw_value", "voltage"),
            ("coulombic_efficiency_raw_value", "coulombic_efficiency"),
            ("energy_density_raw_value", "energy_density"),
            ("conductivity_raw_value", "conductivity"),
        ]:
            if getattr(self, clean, None) is not None:
                continue
            val = getattr(self, raw, None)
            if val is not None and not np.isnan(val):
                setattr(self, clean, val)

        for raw_u, clean in [
            ("capacity_raw_unit", "capacity"),
            ("voltage_raw_unit", "voltage"),
            ("energy_density_raw_unit", "energy_density"),
            ("conductivity_raw_unit", "conductivity"),
        ]:
            if getattr(self, clean, None) is None:      
                continue
            unit = getattr(self, raw_u, None)
            if unit and getattr(self, clean, None) is not None:
                try:
                    getattr(self, clean).unit = unit  
                except Exception:
                    pass

        # present = []
        # if self.capacity is not None:
        #     present.append("capacity")
        # if self.voltage is not None:
        #     present.append("voltage")
        # if self.coulombic_efficiency is not None:
        #     present.append("coulombic_efficiency")
        # if self.energy_density is not None:
        #     present.append("energy_density")
        # if self.conductivity is not None:
        #     present.append("conductivity")

        # self.properties_included = present  

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