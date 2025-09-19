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
from nomad.metainfo import JSON, Quantity, SchemaPackage, SubSection

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


class Battery(EntryData):
    """
    General schema for battery materials data, including bibliographic information
    """

    material_name = Quantity(
        type=str,
        description='The chemical compound name of the battery material.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )
    chemical_formula_hill = Quantity(
        type=str,
        description='The chemical formula of the material, derived from the ' \
        '`extracted_name` and standardized into Hill notation for consistent querying '
        'and analysis.'
    )
    elements = Quantity(
        type=str,
        shape=['*'],
        description="A list of the unique chemical elements present in the material, " \
        "derived from the normalized `extracted_name`."
    )

    # Bibliographic Information
    title = Quantity(
        type=str,
        description='The title of the source scientific publication from which ' \
        'the data was extracted.'
    )
    doi = Quantity(
        type=str,
        description='The Digital Object Identifier (doi) of the source publication, ' \
        'providing a persistent link to the original article.'
    )
    journal = Quantity(
        type=str,
        description='The name of the journal in which the source article was published.'
    )
    date = Quantity(
        type=str,
        description='The full publication date of the source article.'
    )
    publication_year = Quantity(
        type=str,
        description='The year of the publication, extracted for filtering.'
    )
    available_properties = Quantity(
        type=str,
        description='A human-readable list of the properties available in this entry.',
    )
    publication = SubSection(
        section_def=PublicationReference,
        description='The publication reference for this battery data entry.',
    )

    # Quantitative Properties (Normalized)
    capacity = Quantity(
        type=np.float64,
        unit='mA*hour/g',
        description='The normalized specific capacity value.',
    )
    voltage = Quantity(
        type=np.float64,
        unit='V',
        description='The normalized voltage value.',
    )
    coulombic_efficiency = Quantity(
        type=np.float64,
        description='The normalized Coulombic efficiency value (dimensionless).',
    )
    energy_density = Quantity(
        type=np.float64,
        unit='W*hour/kg',
        description='The normalized specific energy value.',
    )
    conductivity = Quantity(
        type=np.float64,
        unit='S/cm',
        description='The normalized conductivity value.',
    )

    def _normalize_publication(
        self, archive: EntryArchive, logger: BoundLogger
    ) -> None:
        if self.doi and not self.publication:
            logger.info(f'Creating Publication Reference section for DOI: {self.doi}')

            pub = PublicationReference()
            pub.DOI_number = self.doi
            self.publication = pub
            self.publication.normalize(archive, logger)

        if self.publication and self.publication.publication_date:
            self.publication_year = str(self.publication.publication_date.year)

    def _set_available_properties(self) -> None:
        property_map = {
            'capacity': 'Capacity',
            'voltage': 'Voltage',
            'coulombic_efficiency': 'Coulombic Efficiency',
            'energy_density': 'Energy Density',
            'conductivity': 'Conductivity',
        }
        present_properties = [
            display_name
            for prop_name, display_name in property_map.items()
            if getattr(self, prop_name) is not None
        ]

        num_properties = len(present_properties)
        Pair_Count = 2
        if not num_properties:
            self.available_properties = 'No quantitative properties'
        elif num_properties == 1:
            self.available_properties = present_properties[0]
        elif num_properties == Pair_Count:
            self.available_properties = ' and '.join(present_properties)
        else:
            all_but_last = ', '.join(present_properties[:-1])
            last = present_properties[-1]
            self.available_properties = f'{all_but_last}, and {last}'

    def normalize(self, archive: EntryArchive, logger: BoundLogger) -> None:
        super().normalize(archive, logger)
        self._normalize_publication(archive, logger)
        self._set_available_properties()


class ChemDataExtractorBattery(Battery):
    
    extracted_name = Quantity(
        type=JSON,
        shape=['*'],
        description='The normalized chemical name, processed by ChemDataExtractor.',
        a_browser=dict(render_value='JsonValue'),
    )

    specifier = Quantity(
        type=str,
        description="The property specifier recognized by the parser which provides " \
        "context to the value, such as 'theoretical' or 'specific' for capacity. " 
    )
    tag = Quantity(
        type=str,
        description="Indicates the origin of the data. For example, energy data is " \
        "tagged as 'CDE' if extracted directly from text using ChemDataExtractor, or "
        "'Calculated' if derived from capacity and voltage measurements via the data " \
        "augmentation process."
    )
    warning = Quantity(
        type=str,
        description="A flag indicating potential issues with the data record. 'S' "
        "(Series) indicates the data is part of a data series; 'R' (Relevance) " \
        "cautions that the source paper may not be primarily about battery materials; "
        "'L' (Limit) indicates the property value is near the plausible physical limits."
    )
    correctness = Quantity(
        type=str,
        description="A manually assigned validation flag ('True' or 'False') " \
        "indicating whether the extracted data correctly matches the source paper. " \
        "This was used on a 500-record subset to evaluate the precision of the " \
        "extraction process."
    )
    info = Quantity(
        type=JSON,
        description='Contains additional contextual information about a property ' \
        'record. For capacity, this can include the cycle number and current value ' \
        'at which the measurement was taken.',
        a_browser=dict(render_value='JsonValue'),
    )

    capacity_raw_value = Quantity(
        type=str,
        description='The capacity value as a string, exactly as it was extracted ' \
        'from the source text before any processing or unit conversion.'
    )
    capacity_raw_unit = Quantity(
        type=str,
        description='The capacity unit as a string, exactly as it was extracted from ' \
        'the source text before normalization. '
    )
    voltage_raw_value = Quantity(
        type=str,
        description='The voltage value as a string, exactly as it was extracted from ' \
        'the source text before any processing or unit conversion.'
    )
    voltage_raw_unit = Quantity(
        type=str,
        description='The voltage unit as a string, exactly as it was extracted from ' \
        'the source text before normalization.'
    )
    coulombic_efficiency_raw_value = Quantity(
        type=str,
        description='The Coulombic efficiency value as a string, exactly as it was ' \
        'extracted from the source text before any processing.'
    )
    coulombic_efficiency_raw_unit = Quantity(
        type=str,
        description='The Coulombic efficiency unit as a string, exactly as it was ' \
        'extracted from the source text before normalization.'
    )
    energy_density_raw_value = Quantity(
        type=str,
        description='The energy value as a string, exactly as it was extracted from ' \
        'the source text before any processing or unit conversion.'
    )
    energy_density_raw_unit = Quantity(
        type=str,
        description='The energy unit as a string, exactly as it was extracted from ' \
        'the source text before normalization.'
    )
    conductivity_raw_value = Quantity(
        type=str,
        description='The conductivity value as a string, exactly as it was extracted ' \
        'from the source text before any processing or unit conversion.'
    )
    conductivity_raw_unit = Quantity(
        type=str,
        description='The conductivity unit as a string, as extracted from the source.',
    )

    def _normalize_material(self, archive: EntryArchive) -> None:
        comp = _parse_composition(self.extracted_name)
        EPSILON = 1e-6
        if comp is None:
            return

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

    def _normalize_quantitative_properties(self) -> None:
        for raw, clean in [
            ('capacity_raw_value', 'capacity'),
            ('voltage_raw_value', 'voltage'),
            ('coulombic_efficiency_raw_value', 'coulombic_efficiency'),
            ('energy_density_raw_value', 'energy_density'),
            ('conductivity_raw_value', 'conductivity'),
        ]:
            if getattr(self, clean, None) is not None:
                continue

            raw_val_str = getattr(self, raw, None)
            if raw_val_str:
                try:
                    num = float(raw_val_str)
                    if not np.isnan(num):
                        setattr(self, clean, num)
                except (ValueError, TypeError):
                    pass

    def normalize(self, archive: EntryArchive, logger: BoundLogger) -> None:
        self._normalize_material(archive)
        self._normalize_quantitative_properties()
        super().normalize(archive, logger)


m_package.__init_metainfo__()