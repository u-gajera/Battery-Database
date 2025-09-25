import ast
from numbers import Number
from typing import TYPE_CHECKING, Any

import numpy as np
from ase.data import atomic_masses, atomic_numbers
from nomad.datamodel.data import EntryData
from nomad.datamodel.metainfo.annotations import ELNAnnotation, ELNComponentEnum
from nomad.datamodel.metainfo.basesections import (
    ElementalComposition,
    PublicationReference,
    CompositeSystem,
    System,
)
from nomad.datamodel.results import Material, Results
from nomad.metainfo import JSON, Quantity, SchemaPackage, SubSection

if TYPE_CHECKING:
    from nomad.datamodel import EntryArchive
    from structlog.stdlib import BoundLogger

m_package = SchemaPackage()


def _format_composition_to_hill(
    composition: dict[str, float],
) -> tuple[list[str], str]:
    EPSILON = 1e-6
    if not composition:
        return [], ''

    elements = sorted(composition.keys())
    if 'C' in elements:
        elements.remove('C')
        elements.insert(0, 'C')
    if 'H' in elements:
        elements.remove('H')
        elements.insert(1 if elements[0] == 'C' else 0, 'H')

    counts = [composition[el] for el in elements]
    formula = ''.join(
        (
            el
            if abs(cnt - 1.0) < EPSILON
            else f'{el}{int(cnt) if float(cnt).is_integer() else cnt}'
        )
        for el, cnt in zip(elements, counts)
    )
    return elements, formula


def _process_composition(
    raw: str | list | None,
) -> tuple[dict[str, float], list[dict[str, float]]] | None:
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

    merged_composition: dict[str, float] = {}
    component_compositions = []
    for part_dict in parts:
        component_comp = {el: float(cnt or 1.0) for el, cnt in part_dict.items()}
        if component_comp:
            component_compositions.append(component_comp)
            for el, count in component_comp.items():
                merged_composition[el] = merged_composition.get(el, 0.0) + count

    return merged_composition, component_compositions


def _calculate_masses(
    composition: dict[str, float],
) -> tuple[float, dict[str, float]]:
    total_mass = 0.0
    element_masses = {}
    for element, count in composition.items():
        Z = atomic_numbers.get(element)
        if Z is None:
            element_mass = 0.0
        else:
            element_mass = atomic_masses[Z]

        total_mass_for_element = element_mass * count
        element_masses[element] = total_mass_for_element
        total_mass += total_mass_for_element
    return total_mass, element_masses


def populate_battery_sample_info(sample: 'Battery', archive: 'EntryArchive') -> None:
    """Populating the CompositeSystem in result section"""

    composition_data = _process_composition(sample.chemical_composition)
    if composition_data is None:
        return

    merged_composition, component_compositions = composition_data
    overall_elements, overall_formula = _format_composition_to_hill(
        merged_composition
    )

    if not overall_elements:
        return

    if archive.results is None:
        archive.results = Results()
    mat: Material = getattr(archive.results, 'material', None) or Material()
    archive.results.material = mat

    sample.elements = overall_elements
    if not sample.chemical_formula_hill:
        sample.chemical_formula_hill = overall_formula

    mat.chemical_formula_hill = sample.chemical_formula_hill
    mat.elements = sample.elements
    mat.nelements = len(sample.elements)

    total_mass_overall, element_masses_overall = _calculate_masses(merged_composition)
    total_atoms_overall = sum(merged_composition.values())

    if total_atoms_overall > 0:
        mat.elemental_composition = []
        for element, count in merged_composition.items():
            mass_frac = (
                element_masses_overall.get(element, 0.0) / total_mass_overall
                if total_mass_overall > 0
                else 0.0
            )
            mat.elemental_composition.append(
                ElementalComposition(
                    element=element,
                    atomic_fraction=count / total_atoms_overall,
                    mass=element_masses_overall.get(element, 0.0),
                    mass_fraction=mass_frac,
                )
            )

    component_systems = []
    for comp_dict in component_compositions:
        elements, formula = _format_composition_to_hill(comp_dict)
        if not elements:
            continue

        total_mass_component, element_masses_component = _calculate_masses(comp_dict)
        total_atoms_component = sum(comp_dict.values())
        elemental_compositions_component = []

        if total_atoms_component > 0:
            for element, count in comp_dict.items():
                mass_frac = (
                    element_masses_component.get(element, 0.0) / total_mass_component
                    if total_mass_component > 0
                    else 0.0
                )
                elemental_compositions_component.append(
                    ElementalComposition(
                        element=element,
                        atomic_fraction=count / total_atoms_component,
                        mass=element_masses_component.get(element, 0.0),
                        mass_fraction=mass_frac,
                    )
                )

        system_component = System(
            elements=elements,
            chemical_formula_hill=formula,
            elemental_composition=elemental_compositions_component,
        )
        component_systems.append(system_component)

    if len(component_systems) > 1:
        mat.system = CompositeSystem(components=component_systems)
    elif len(component_systems) == 1:
        mat.system = component_systems[0]


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
    chemical_composition = Quantity(
    type=JSON,
    shape=['*'],
    description='A list of dictionaries defining the material composition as a JSON array.',
    a_eln=ELNAnnotation(component=ELNComponentEnum.RichTextEditQuantity),  
    a_browser=dict(render_value='JsonValue'), 
    )

    # Bibliographic Information
    doi = Quantity(
        type=str,
        description='The Digital Object Identifier (doi) of the source publication, ' \
        'providing a persistent link to the original article.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
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
        a_eln=ELNAnnotation(component=ELNComponentEnum.NumberEditQuantity),
    )
    voltage = Quantity(
        type=np.float64,
        unit='V',
        description='The normalized voltage value.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.NumberEditQuantity),
    )
    coulombic_efficiency = Quantity(
        type=np.float64,
        description='The normalized Coulombic efficiency value (dimensionless).',
        a_eln=ELNAnnotation(component=ELNComponentEnum.NumberEditQuantity),
    )
    energy_density = Quantity(
        type=np.float64,
        unit='W*hour/kg',
        description='The normalized specific energy value.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.NumberEditQuantity),
    )
    conductivity = Quantity(
        type=np.float64,
        unit='S/cm',
        description='The normalized conductivity value.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.NumberEditQuantity),
    )

    def _normalize_publication(
        self, archive: 'EntryArchive', logger: 'BoundLogger'
    ) -> None:
        if self.doi and not self.publication:
            logger.info(f'Creating Publication Reference section for DOI: {self.doi}')
            pub = PublicationReference(DOI_number=self.doi)
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
            self.available_properties = (
                f'{", ".join(present_properties[:-1])}, and {present_properties[-1]}'
            )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        super().normalize(archive, logger)
        populate_battery_sample_info(self, archive)
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
        "'Calculated' if derived from capacity or voltage measurements via the data " \
        "augmentation process."
    )
    warning = Quantity(
        type=str,
        description="A flag indicating potential issues with the data record. 'S' "
        "(Series) indicates the data is part of a data series; 'R' (Relevance) " \
        "cautions that the source paper may not be primarily about battery materials; "
        "'L' (Limit) indicates the value is near the plausible physical limits."
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

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        if self.extracted_name and self.chemical_composition is None:
            self.chemical_composition = self.extracted_name

        self._normalize_quantitative_properties()
        super().normalize(archive, logger)


m_package.__init_metainfo__()