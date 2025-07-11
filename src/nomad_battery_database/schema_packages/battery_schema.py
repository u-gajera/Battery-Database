from __future__ import annotations

import ast
from numbers import Number
from typing import TYPE_CHECKING, Any

import numpy as np
from nomad.datamodel.data import EntryData
from nomad.datamodel.metainfo.annotations import ELNAnnotation, ELNComponentEnum
from nomad.datamodel.metainfo.basesections import (
    ElementalComposition,
    PublicationReference,
)
from nomad.datamodel.results import Material, Results
from nomad.metainfo import Quantity, SchemaPackage, SubSection

if TYPE_CHECKING:
    from nomad.datamodel import EntryArchive
    from structlog.stdlib import BoundLogger

m_package = SchemaPackage()

def _parse_composition(
    raw: str | list | None,
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
            try:
                count = float(cnt or 1.0)
                totals[el] = totals.get(el, 0.0) + count
            except (ValueError, TypeError):
                pass
    elems = sorted(totals)
    if 'C' in elems:
        elems.remove('C')
        elems.insert(0, 'C')
    if 'H' in elems:
        elems.remove('H')
        elems.insert(1 if elems[0] == 'C' else 0, 'H')
    counts = [totals[e] for e in elems]
    return elems, counts


def _to_number(val: Any) -> float | None:
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None
    if hasattr(val, 'magnitude'):
        try:
            return float(val.to_base_units().magnitude)
        except Exception:
            return float(val.magnitude)
    if isinstance(val, Number):
        return float(val)
    return None


class BatteryDatabase(EntryData):
    material_name = Quantity(
        type=str, a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity)
    )
    extracted_name = Quantity(type=str)
    chemical_formula_hill = Quantity(type=str)
    elements = Quantity(type=str, shape=['*'])
    title = Quantity(type=str)
    DOI = Quantity(type=str)
    journal = Quantity(type=str)
    date = Quantity(type=str)

    specifier = Quantity(type=str)
    tag = Quantity(type=str)
    warning = Quantity(type=str)
    correctness = Quantity(type=str)
    info = Quantity(type=str)
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

    capacity = Quantity(type=np.float64, unit='mA*hour/g')
    voltage = Quantity(type=np.float64, unit='V')
    coulombic_efficiency = Quantity(type=np.float64)
    energy_density = Quantity(type=np.float64, unit='W*hour/kg')
    conductivity = Quantity(type=np.float64, unit='S/cm')
    publication_year = Quantity(
        type=str,
        description='The year of the publication, extracted for filtering.'
    )
    publication = SubSection(
        section_def=PublicationReference,
        description='The publication reference for this battery data entry.'
    )

    def normalize(self, archive: EntryArchive, logger: BoundLogger) -> None:
        super().normalize(archive, logger)

        comp = _parse_composition(self.extracted_name)
        EPSILON = 1e-6
        if comp is not None:
            elements, counts = comp
            self.elements = elements
            if not self.chemical_formula_hill:
                self.chemical_formula_hill = ''.join(
                    (
                        el
                        if abs(cnt - 1.0) < EPSILON
                        else f'{el}{int(cnt) if float(cnt).is_integer() else cnt}'
                    )
                    for el, cnt in zip(elements, counts)
                )
            if archive.results is None:
                archive.results = Results()
            mat: Material = getattr(archive.results, 'material', None) or Material()
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
            ('capacity_raw_value', 'capacity'),
            ('voltage_raw_value', 'voltage'),
            ('coulombic_efficiency_raw_value', 'coulombic_efficiency'),
            ('energy_density_raw_value', 'energy_density'),
            ('conductivity_raw_value', 'conductivity'),
        ]:
            if getattr(self, clean, None) is not None:
                continue
            val = getattr(self, raw, None)
            if val is not None and not np.isnan(val):
                setattr(self, clean, val)

        for raw_u, clean in [
            ('capacity_raw_unit', 'capacity'),
            ('voltage_raw_unit', 'voltage'),
            ('energy_density_raw_unit', 'energy_density'),
            ('conductivity_raw_unit', 'conductivity'),
        ]:
            if getattr(self, clean, None) is None:
                continue
            unit = getattr(self, raw_u, None)
            if unit and getattr(self, clean, None) is not None:
                try:
                    getattr(self, clean).unit = unit
                except Exception:
                    pass

        if self.DOI and not self.publication:
            logger.info(f"Creating Publication Reference section for DOI: {self.DOI}")

            pub = PublicationReference()
            pub.DOI_number = self.DOI
            self.publication = pub

            self.publication.normalize(archive, logger)
        
        if self.publication and self.publication.publication_date:
            self.publication_year = self.publication.publication_date.year

m_package.__init_metainfo__()

__all__ = ['m_package', 'BatteryDatabase']