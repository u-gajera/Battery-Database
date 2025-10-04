import ast
from typing import TYPE_CHECKING, Union

import numpy as np
from ase.data import atomic_masses, atomic_numbers
from nomad.datamodel.data import EntryData
from nomad.datamodel.metainfo.annotations import ELNAnnotation, ELNComponentEnum
from nomad.datamodel.metainfo.basesections import (
    CompositeSystem,
    ElementalComposition,
    PublicationReference,
    PureSubstanceComponent,
    PureSubstanceSection,
)
from nomad.datamodel.results import Material, Results
from nomad.metainfo import JSON, Quantity, SchemaPackage, SubSection

if TYPE_CHECKING:
    from nomad.datamodel import EntryArchive
    from structlog.stdlib import BoundLogger

m_package = SchemaPackage()

def _process_composition(
    raw: Union[str, list, None],
) -> Union[list[dict[str, Union[float, str]]], None]:
    """
    Parses the raw composition input into a list of component compositions.
    Coefficients are converted to float if possible, otherwise kept as strings.
    """
    if raw is None:
        return None
    try:
        parts = ast.literal_eval(raw) if isinstance(raw, str) else raw
    except (ValueError, SyntaxError):
        return None

    if not isinstance(parts, list) or not all(isinstance(p, dict) for p in parts):
        return None

    component_compositions = []
    for part_dict in parts:
        component_comp = {}
        for el, cnt in part_dict.items():
            try:
                component_comp[el] = float(cnt)
            except (ValueError, TypeError):
                component_comp[el] = str(cnt)
        if component_comp:
            component_compositions.append(component_comp)
    return component_compositions


def _format_composition_to_formula(
    composition: dict[str, Union[float, str]],
) -> tuple[list[str], str]:
    """
    Formats a composition dictionary into a Hill notation formula string,
    handling both numeric and string coefficients.
    """
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

    formula_parts = []
    for el in elements:
        cnt = composition[el]
        part = el
        is_one = False
        if isinstance(cnt, (int, float)):
            if abs(cnt - 1.0) < EPSILON:
                is_one = True
        elif str(cnt) in ['1', '1.0']:
            is_one = True

        if not is_one:
            if isinstance(cnt, (int, float)):
                part += f'{int(cnt) if float(cnt).is_integer() else cnt}'
            else:
                str_cnt = str(cnt)
                part += f'({str_cnt})' if not str_cnt.isalnum() else str_cnt
        formula_parts.append(part)

    return elements, ''.join(formula_parts)


def _calculate_masses(
    composition: dict[str, float],
) -> tuple[float, dict[str, float]]:
    """
    Calculates the total mass and individual element masses from a composition dict."""
    total_mass = 0.0
    element_masses = {}
    for element, count in composition.items():
        Z = atomic_numbers.get(element)
        element_mass = atomic_masses[Z] if Z is not None else 0.0
        total_mass_for_element = element_mass * count
        element_masses[element] = total_mass_for_element
        total_mass += total_mass_for_element
    return total_mass, element_masses


def populate_battery_sample_info(sample: 'Battery',  # noqa: PLR0912, PLR0915
                                 archive: 'EntryArchive', 
                                 logger: 'BoundLogger') -> None: 
    """
    Processes the chemical composition from 'extracted_name' to populate the
    sample section itself with PureSubstanceComponents.
    """
    component_compositions = _process_composition(sample.extracted_name)
    if not component_compositions:
        return

    component_list = []
    all_elements = set()
    all_components_numeric = True

    for comp_dict in component_compositions:
        elements, formula = _format_composition_to_formula(comp_dict)
        if not elements:
            continue
        all_elements.update(elements)
        is_comp_numeric = all(isinstance(v, (int, float)) for v in comp_dict.values())
        if not is_comp_numeric:
            all_components_numeric = False

        elemental_compositions_component = []
        if is_comp_numeric:
            numeric_comp_dict = {el: float(v) for el, v in comp_dict.items()}
            total_mass, masses = _calculate_masses(numeric_comp_dict)
            total_atoms = sum(numeric_comp_dict.values())
            if total_atoms > 0:
                for el, count in numeric_comp_dict.items():
                    if total_mass > 0:
                        mass_frac = masses.get(el, 0) / total_mass
                    else:
                        mass_frac = 0
                    elemental_compositions_component.append(
                        ElementalComposition(
                            element=el,
                            atomic_fraction=count / total_atoms,
                            mass_fraction=mass_frac,
                        )
                    )

        substance = PureSubstanceSection( 
            molecular_formula=formula,    
            #elements=elements,
            elemental_composition=elemental_compositions_component or None,
        )

        component = PureSubstanceComponent(pure_substance=substance)
        component_list.append(component)

    sample.components = component_list
    sample.elements = sorted(list(all_elements))

    formulas = [
        comp.pure_substance.molecular_formula
        for comp in component_list
        if comp.pure_substance
    ]
    if not sample.chemical_formula_hill:
        sample.chemical_formula_hill = ' & '.join(formulas)

    if all_components_numeric:
        merged_composition = {}
        for comp_dict in component_compositions:
            for el, count in comp_dict.items():
                merged_composition[el] = merged_composition.get(el, 0.0) + float(count)

        total_mass, masses = _calculate_masses(merged_composition)
        total_atoms = sum(merged_composition.values())
        if total_atoms > 0:
            sample.elemental_composition = []
            for el, count in merged_composition.items():
                if total_mass > 0:
                    mass_fraction = masses.get(el, 0) / total_mass
                else:
                    mass_fraction = 0

                sample.elemental_composition.append(
                    ElementalComposition(
                        element=el,
                        atomic_fraction=count / total_atoms,
                        mass_fraction=mass_fraction,
                    )
                )
    else:
        sample.elemental_composition = [
            ElementalComposition(element=el) for el in sample.elements
        ]
    
    if sample.elemental_composition:
        if archive.results is None:
            archive.results = Results()
        if archive.results.material is None:
            archive.results.material = Material()

        mat = archive.results.material
        mat.elements = sample.elements
        mat.nelements = len(sample.elements)
        mat.chemical_formula_hill = sample.chemical_formula_hill
        
        element_to_fraction = {
            comp.element: comp.atomic_fraction 
            for comp in sample.elemental_composition 
            if comp.atomic_fraction is not None
        }
        
        if len(element_to_fraction) == len(mat.elements):
             mat.elements_ratios = [element_to_fraction[el] for el in mat.elements]

        archive.results.elemental_composition = sample.elemental_composition

def sanitize_string(input_str: Union[str, None]) -> Union[str, None]:
    """
    Replaces various Unicode dash and minus characters with a standard hyphen.
    From the ChemDataExtractor, there are some instances of these characters
    """
    if input_str is None:
        return None
    
    replacements = {
        '\u2212': '-',  
        '\u2013': '-', 
        '\u2014': '-',
    }
    
    sanitized_str = input_str
    for old, new in replacements.items():
        sanitized_str = sanitized_str.replace(old, new)
    return sanitized_str


class Battery(CompositeSystem, EntryData):
    """
    General schema for battery materials data, including bibliographic information
    """
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

    material_name = Quantity(
        type=str,
        description='The Digital Object Identifier (doi) of the source publication, ' \
        'providing a persistent link to the original article.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )
    available_properties = Quantity(
        type=str,
        description='A human-readable list of the properties available in this entry.',
    )
    publication = SubSection(
        section_def=PublicationReference,
        description='The publication reference for this battery data entry.',
    )
    capacity = Quantity(
        type=np.float64,
        unit='mA*hour/g',
        description='Battery capacity is a measure of how much electrical charge a '
        'cell (or electrode material) can deliver (or store) under a defined set of '
        'operating conditions. In materials science, one often distinguishes '
        'between specific capacity (gravimetric), which is charge per unit mass '
        '(e.g., mAh/g), and volumetric capacity, which is charge per unit volume '
        '(e.g., mAh/cm³). The reported capacity often depends on experimental '
        'conditions like the number of cycles and current density. This schema '
        'stores the normalized specific capacity.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.NumberEditQuantity),
    )
    voltage = Quantity(
        type=np.float64,
        unit='V',
        description='Voltage in a battery is the electrical potential difference '
        'between the two electrodes (cathode and anode), which drives the flow of '
        'electrons. It can be reported as open-circuit voltage (no current), '
        'operating/nominal voltage (under load), or as a voltage profile that '
        'varies with the state of charge. This value reflects the thermodynamics '
        'of the redox reactions and internal resistances of the battery.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.NumberEditQuantity),
    )
    coulombic_efficiency = Quantity(
        type=np.float64,
        description='Coulombic efficiency, also known as Faradaic efficiency, is a '
        'measure of charge transfer efficiency in a battery. It is the ratio of '
        'the total charge extracted from the battery during discharging to the '
        'total charge put into the battery during charging. An efficiency close '
        'to 100% indicates minimal charge loss to side reactions, such as '
        'electrolyte decomposition or irreversible capacity loss.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.NumberEditQuantity),
    )
    energy_density = Quantity(
        type=np.float64,
        unit='W*hour/kg',
        description='Specific energy (or gravimetric energy density) quantifies the '
        'amount of energy a battery material can store per unit mass, typically '
        'measured in watt-hours per kilogram (Wh/kg). It is a key performance '
        'metric calculated from the specific capacity and operating voltage. This '
        'schema also considers energy density per unit volume (volumetric energy '
        'density), measured in watt-hours per liter (Wh/L).',
        a_eln=ELNAnnotation(component=ELNComponentEnum.NumberEditQuantity),
    )
    conductivity = Quantity(
        type=np.float64,
        unit='S/cm',
        description='Conductivity measures a material\'s ability to conduct electric '
        'charge. In the context of batteries, this can refer to electronic '
        'conductivity (movement of electrons through electrodes) or ionic '
        'conductivity (movement of ions through the electrolyte or electrodes). '
        'Good conductivity is crucial for efficient charge transport and overall '
        'battery performance. This schema stores the normalized conductivity value, '
        'without distinguishing between ionic and electronic contributions.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.NumberEditQuantity),
    )

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
        self._set_available_properties()
        super().normalize(archive, logger)
        


class ChemDataExtractorBattery(Battery):
    """
    Schema for battery materials data extracted using ChemDataExtractor (CDE),
    including bibliographic information and raw extracted values."""
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
        shape=['*'],
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
        description='The conductivity value as a string, exactly as it was extracted '\
        'from the source text before any processing or unit conversion.'
    )
    conductivity_raw_unit = Quantity(
        type=str,
        description='The conductivity unit as a string, as extracted from the source.',
    )
    publication = SubSection(
        section_def=PublicationReference,
        description='The publication reference for this battery data entry.',
    )
    doi = Quantity(
        type=str,
        description='The Digital Object Identifier (doi) of the source publication, '
        'providing a persistent link to the original article.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )
    publication_year = Quantity(
        type=str, description='The year of the publication, extracted for filtering.'
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
        if self.material_name:
            logger.info(f"Sanitizing material_name: '{self.material_name}'")
            self.material_name = sanitize_string(self.material_name)
        super().normalize(archive, logger)
        self._normalize_quantitative_properties()
        populate_battery_sample_info(self, archive, logger)
        self._normalize_publication(archive, logger)

m_package.__init_metainfo__()