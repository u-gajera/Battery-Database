from __future__ import annotations

import ast
from typing import TYPE_CHECKING

import numpy as np
from nomad.datamodel.data import Schema
from nomad.datamodel.metainfo.annotations import ELNAnnotation, ELNComponentEnum
from nomad.datamodel.metainfo.basesections import ElementalComposition
from nomad.datamodel.results import Material, Results
from nomad.metainfo import Quantity, SchemaPackage, Section, SubSection

if TYPE_CHECKING:  # pragma: no cover
    from nomad.datamodel import EntryArchive
    from structlog.stdlib import BoundLogger

m_package = SchemaPackage()

# Helper – parse the Extracted_name field                                       #
def _parse_composition(raw: str | list | None) -> tuple[list[str], list[float]] | None:
    """Return (elements, counts) in Hill order or *None* if parsing fails."""
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
            try:
                cnt_f = float(cnt)
            except Exception:
                cnt_f = 1.0
            totals[el] = totals.get(el, 0.0) + cnt_f

    elems = sorted(totals)
    if "C" in elems:
        elems.remove("C")
        elems.insert(0, "C")
    if "H" in elems:
        elems.remove("H")
        elems.insert(1 if elems[0] == "C" else 0, "H")

    counts = [totals[e] for e in elems]
    return elems, counts

# BatteryProperties section                                                  #

class BatteryProperties(Schema):
    """Metadata extracted from one publication / one material."""

    # --- bibliographic ---------------------------------------------------- #
    material_name = Quantity(type=str, 
                    a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity))
    extracted_name = Quantity(type=str)
    chemical_formula_hill = Quantity(type=str)
    elements = Quantity(type=str, shape=["*"])
    title = Quantity(type=str)
    DOI = Quantity(type=str)
    journal = Quantity(type=str)
    date = Quantity(type=str)

    # --- metadata --------------------------------------------------------- #
    specifier = Quantity(type=str)
    tag = Quantity(type=str)
    warning = Quantity(type=str)
    correctness = Quantity(type=str)
    material_type = Quantity(type=str)
    info = Quantity(type=str)

    # --- raw numerical ---------------------------------------------------- #
    capacity_raw_value = Quantity(type=np.float64)
    capacity_raw_unit = Quantity(type=str)
    voltage_raw_value = Quantity(type=np.float64)
    voltage_raw_unit = Quantity(type=str)
    coulombic_efficiency_raw_value = Quantity(type=np.float64)
    coulombic_efficiency_raw_unit = Quantity(type=str)
    energy_density_raw_value = Quantity(type=np.float64)
    energy_density_raw_unit = Quantity(type=str)
    conductivity_raw_value = Quantity(type=np.float64)
    conductivity_raw_unit = Quantity(type=str)

    # --- normalised numbers ---------------------------------------------- #
    capacity = Quantity(type=np.float64, unit="mA*hour/g")
    voltage = Quantity(type=np.float64, unit="V")
    coulombic_efficiency = Quantity(type=np.float64)
    energy_density = Quantity(type=np.float64, unit="W*hour/kg")
    conductivity = Quantity(type=np.float64, unit="S/cm")

    # normaliser                                                            #
    def normalize(self, archive: EntryArchive, logger: BoundLogger) -> None:
        super().normalize(archive, logger)

        # --- 1) composition ---------------------------------------------- #
        comp = _parse_composition(self.extracted_name)
        if comp is not None:
            elements, counts = comp
            self.elements = elements

            # chemical_formula_hill (if missing)
            if not self.chemical_formula_hill:
                parts = []
                for el, cnt in zip(elements, counts):
                    if abs(cnt - 1.0) < 1e-6:
                        parts.append(el)
                    else:
                        cnt_str=str(int(cnt)) if abs(cnt - int(cnt))<1e-6 else str(cnt)
                        parts.append(f"{el}{cnt_str}")
                self.chemical_formula_hill = "".join(parts)

            # --- NEW: results.material & elemental_composition ------------ #
            if archive.results is None:
                archive.results = Results()           # type: ignore

            mat = getattr(archive.results, "material", None)
            if mat is None:
                mat = Material()
                archive.results.material = mat        # type: ignore

            total = float(sum(counts))
            mat.chemical_formula_hill = self.chemical_formula_hill
            mat.elements            = elements        # type: ignore
            mat.nelements           = len(elements)   # type: ignore
            mat.elements_ratios     = [c / total for c in counts]  # type: ignore

            ecs = []
            for el, cnt in zip(elements, counts):
                ec = ElementalComposition()
                ec.element         = el
                ec.atomic_fraction = cnt / total
                ecs.append(ec)
            archive.results.elemental_composition = ecs  # type: ignore

        # --- copy *_raw_value → clean fields --------------------------- #
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

        # --- unit strings --------------------------------------------- #
        for raw_u, clean in [
            ("capacity_raw_unit", "capacity"),
            ("voltage_raw_unit", "voltage"),
            ("energy_density_raw_unit", "energy_density"),
            ("conductivity_raw_unit", "conductivity"),
        ]:
            unit = getattr(self, raw_u, None)
            if unit and getattr(self, clean, None) is not None:
                try:
                    getattr(self, clean).unit = unit  # type: ignore[attr-defined]
                except Exception:
                    pass  # running outside real NOMAD context


class BatteryDatabase(Schema):
    m_def = Section(label="Battery database", 
                    extends=["nomad.datamodel.data.EntryData"])
    Material_entries = SubSection(sub_section=BatteryProperties, 
                                  repeats=True)

m_package.__init_metainfo__()

__all__ = ["m_package", "BatteryProperties", "BatteryDatabase"]