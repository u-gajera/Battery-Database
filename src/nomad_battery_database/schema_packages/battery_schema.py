from typing import TYPE_CHECKING
import numpy as np
import ast # Ensure ast is imported

from nomad.datamodel.data import Schema
from nomad.metainfo import Quantity, SchemaPackage, Section, SubSection
from nomad.datamodel.metainfo.annotations import ELNAnnotation, ELNComponentEnum


if TYPE_CHECKING:  # pragma: no cover
    from nomad.datamodel import EntryArchive
    from structlog.stdlib import BoundLogger

m_package = SchemaPackage()

class BatteryProperties(Schema):
    """Data extracted from one publication / one material."""

    # bibliographic
    material_name = Quantity(type=str, a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity))
    extracted_name = Quantity(type=str) # String representation of list of dicts
    chemical_formula_hill = Quantity(type=str)
    elements = Quantity(type=str)
    title = Quantity(type=str)
    DOI = Quantity(type=str)
    journal = Quantity(type=str)
    date = Quantity(type=str)

    # meta
    specifier = Quantity(type=str)
    tag = Quantity(type=str)
    warning = Quantity(type=str)
    correctness = Quantity(type=str)
    material_type = Quantity(type=str)
    info = Quantity(type=str)

    # raw numbers
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

    # aliases w/ units – mapped in normalize
    capacity = Quantity(type=np.float64, unit="mA*hour/g")
    voltage = Quantity(type=np.float64, unit="V")
    coulombic_efficiency = Quantity(type=np.float64)
    energy_density = Quantity(type=np.float64, unit="W*hour/kg")
    conductivity = Quantity(type=np.float64, unit="S/cm")

    elements = Quantity(
        type=str,
        shape=['*'],
        description='A list of unique chemical elements present in the material, derived from extracted_name.',
        a_eln=ELNAnnotation(label='Elements Present')
    )

    def normalize(self, archive: "EntryArchive", logger: "BoundLogger") -> None:  # noqa: D401
        super().normalize(archive, logger)

        entry_log_prefix = f"[EntryID: {archive.metadata.entry_id if archive.metadata else 'N/A'}] "
        logger.info(
            f"{entry_log_prefix}Starting normalization of BatteryProperties. "
            f"Initial extracted_name: '{self.extracted_name}', type: {type(self.extracted_name)}"
        )

        parsed_list_for_elements = []
        if self.extracted_name and isinstance(self.extracted_name, str):
            try:
                # The extracted_name is a string like "[{'Fe': '1'}, {'O': '1'}]"
                evaluated_content = ast.literal_eval(self.extracted_name)

                if isinstance(evaluated_content, list):
                    parsed_list_for_elements = evaluated_content
                    logger.info(
                        f"{entry_log_prefix}Successfully parsed 'extracted_name' string into a list: {parsed_list_for_elements}"
                    )
                else:
                    logger.warning(
                        f"{entry_log_prefix}'extracted_name' string ('{self.extracted_name}') "
                        f"did not evaluate to a list. Evaluated type: {type(evaluated_content)}"
                    )
            except (ValueError, SyntaxError) as e:
                logger.warning(
                    f"{entry_log_prefix}SyntaxError or ValueError while parsing 'extracted_name' string "
                    f"'{self.extracted_name}': {e}"
                )
            except Exception as e:
                logger.error(
                    f"{entry_log_prefix}Unexpected error while parsing 'extracted_name' string "
                    f"'{self.extracted_name}': {e}"
                )
        elif self.extracted_name:
            logger.warning(
                f"{entry_log_prefix}'extracted_name' was present but not a string as expected in normalize. "
                f"Value: '{self.extracted_name}', Type: {type(self.extracted_name)}. "
                "This might indicate an issue with how it was set by the parser or schema type coercion."
            )
        else:
            logger.info(f"{entry_log_prefix}'extracted_name' is empty or None. No elements will be derived.")

        unique_elements = set()
        if parsed_list_for_elements: # Proceed only if parsing was successful and yielded a list
            for item in parsed_list_for_elements:
                if isinstance(item, dict):
                    for element_symbol in item.keys():
                        if isinstance(element_symbol, str) and element_symbol.isalpha(): # Basic check for valid element symbol
                            unique_elements.add(element_symbol)
                        else:
                            logger.warning(
                                f"{entry_log_prefix}Invalid or non-string element key found in parsed list item: "
                                f"'{element_symbol}' in item '{item}'"
                            )
                else:
                    logger.warning(
                        f"{entry_log_prefix}Item in parsed 'extracted_name' list is not a dict: '{item}'"
                    )

            if unique_elements:
                self.elements = sorted(list(unique_elements))
                logger.info(
                    f"{entry_log_prefix}Successfully populated 'self.elements': {self.elements}"
                )
            else:
                logger.info(
                    f"{entry_log_prefix}No unique elements derived from parsed list: {parsed_list_for_elements}. "
                    "'self.elements' will be empty."
                )
        elif self.extracted_name: # If extracted_name was present but parsing failed or yielded no valid structure
            logger.warning(
                f"{entry_log_prefix}'self.elements' not populated because 'extracted_name' parsing "
                f"failed or yielded no parsable structure. Original 'extracted_name': '{self.extracted_name}'"
            )

        # If self.elements was not set, ensure it's an empty list to avoid None values if expected to be list
        if self.elements is None:
            self.elements = []
            logger.info(f"{entry_log_prefix}Ensuring 'self.elements' is an empty list as it was not populated.")


        # Normalize other properties (as before)
        if self.capacity_raw_value is not None:
            self.capacity = self.capacity_raw_value
        if self.voltage_raw_value is not None:
            self.voltage = self.voltage_raw_value
        if self.coulombic_efficiency_raw_value is not None:
            self.coulombic_efficiency = self.coulombic_efficiency_raw_value
        if self.energy_density_raw_value is not None:
            self.energy_density = self.energy_density_raw_value
        if self.conductivity_raw_value is not None:
            self.conductivity = self.conductivity_raw_value

class BatteryDatabase(Schema):
    m_def = Section(label="Battery database", extends=["nomad.datamodel.data.EntryData"])
    Material_entries = SubSection(sub_section=BatteryProperties, repeats=True)

m_package.__init_metainfo__()

__all__ = ["m_package", "BatteryProperties", "BatteryDatabase"]
