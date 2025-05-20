from typing import TYPE_CHECKING
import numpy as np

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
    extracted_name = Quantity(type=str)
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

    def normalize(self, archive: "EntryArchive", logger: "BoundLogger") -> None:  # noqa: D401
        super().normalize(archive, logger)
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
