from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import EntryArchive
    from structlog.stdlib import BoundLogger

from nomad.datamodel.data import Schema
from nomad.datamodel.metainfo.annotations import ELNAnnotation, ELNComponentEnum
from nomad.metainfo import (
    Quantity,
    SchemaPackage,
    Section,
    SubSection,
)

#######################################
# Schema definitions
#######################################

m_package = SchemaPackage()

class BatteryProperties(Schema):
    """All data extracted for a single entry (row) in the battery database."""

    # ------------------------------------------------------------------
    # Material identifiers
    # ------------------------------------------------------------------
    material_name = Quantity(
        type=str,
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
        description="Material name exactly as stated in the publication (column *Name*)."
    )

    extracted_name = Quantity(
        type=str,
        description="Chemically-normalized compound name (column *Extracted_name*)."
    )
    title = Quantity(type=str, description="Publication title.")
    DOI = Quantity(type=str, description="Digital Object Identifier.")
    journal = Quantity(type=str, description="Journal title.")
    date = Quantity(type=str, description="Publication date (ISO yyyy-mm-dd).")

    specifier = Quantity(type=str, description="Exact text used to identify the property.")
    tag = Quantity(type=str, description="Extraction tag: *CDE* (direct) or *CALC* (calculated).")
    warning = Quantity(type=str, description="Quality flag: S – series, R – relevance, L – limit.")

    correctness = Quantity(type=str, description="Manual evaluation of extraction correctness.")

    material_type = Quantity(type=str, description="Battery role: anode, cathode, electrolyte …")

    info = Quantity(type=str, description="Additional context (current, cycle number, etc.).")

    # capacity_value = Quantity(type=np.float64, unit="mA*hour/g",
    #                           description="Normalised specific capacity.")
    # voltage_value = Quantity(type=np.float64, unit="V", description="Normalised voltage.")
    # coulombic_efficiency_value = Quantity(type=np.float64,
    #                                       description="Normalised Coulombic efficiency (fraction or %).")
    # energy_density_value = Quantity(type=np.float64, unit="W*hour/kg", description="Normalised specific energy.")
    # conductivity_value = Quantity(type=np.float64, unit="S/cm", description="Normalised conductivity.")

    # ------------------------------------------------------------------
    # raw values and units
    # raw values are 
    # ------------------------------------------------------------------
    capacity_raw_value = Quantity(type=np.float64, description="Raw capacity value.")
    capacity_raw_unit = Quantity(type=str, description="Raw capacity unit.")

    voltage_raw_value = Quantity(type=np.float64, description="Raw voltage value.")
    voltage_raw_unit = Quantity(type=str, description="Raw voltage unit.")

    coulombic_efficiency_raw_value = Quantity(type=np.float64, description="Raw CE value.")
    coulombic_efficiency_raw_unit = Quantity(type=str, description="Raw CE unit.")

    energy_density_raw_value = Quantity(type=np.float64, description="Raw specific-energy value.")
    energy_density_raw_unit = Quantity(type=str, description="Raw specific-energy unit.")

    conductivity_raw_value = Quantity(type=np.float64, description="Raw conductivity value.")
    conductivity_raw_unit = Quantity(type=str, description="Raw conductivity unit.")

    # ------------------------------------------------------------------
    # Normalised values and units
    # ------------------------------------------------------------------
    # capacity_unit = Quantity(type=str, description="Normalised capacity unit.", default="mA*hour/g")
    # voltage_unit = Quantity(type=str, description="Normalised voltage unit.", default="V")
    # coulombic_efficiency_unit = Quantity(type=str, description="Normalised CE unit.")
    # energy_unit = Quantity(type=str, description="Normalised energy unit.", default="W*hour/kg")
    # conductivity_unit = Quantity(type=str, description="Normalised conductivity unit.", default="S/cm")

    # ------------------------------------------------------------------
    # Legacy aliases
    # ------------------------------------------------------------------
    capacity = Quantity(type=np.float64, 
                        unit="mA*hour/g",
                        description="Alias for *capacity_value* (legacy).")
    voltage  = Quantity(type=np.float64, 
                        unit="V", 
                        description="Alias for *voltage_value* (legacy).")
    coulombic_efficiency = Quantity(type=np.float64, 
                        description="Alias for *coulombic_efficiency_value* (legacy).")
    energy_density = Quantity(type=np.float64, 
                        unit="W*hour/kg",
                        description="Alias for *energy_density_value* (legacy).")
    conductivity = Quantity(type=np.float64, 
                        unit="S/cm",
                        description="Alias for *conductivity_value* (legacy).")

    # ------------------------------------------------------------------
    # Normalisation hook 
    # ------------------------------------------------------------------
    def normalize(self, 
                  archive: 'EntryArchive', 
                  logger: 'BoundLogger') -> None:
        super().normalize(archive, logger)
        if self.capacity_value is not None:
            self.capacity = self.capacity_value
        if self.voltage_value is not None:
            self.voltage = self.voltage_value
        if self.coulombic_efficiency_value is not None:
            self.coulombic_efficiency = self.coulombic_efficiency_value
        if self.energy_density_value is not None:
            self.energy_density = self.energy_density_value
        if self.conductivity_value is not None:
            self.conductivity = self.conductivity_value

class BatteryDatabase(Schema):
    m_def = Section(label="Battery database", 
                    extends=["nomad.datamodel.data.EntryData"])
    Material_entries = SubSection(sub_section=BatteryProperties, 
                           repeats=True)

m_package.__init_metainfo__()