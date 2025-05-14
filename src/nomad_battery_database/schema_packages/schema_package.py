#mostly copy paste from the RDM example
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

m_package = SchemaPackage()

class BatteryProperties(Schema):

    material_name = Quantity(
        type=str,
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
        description="Name of the material used in the battery."
    )

    capacity = Quantity(
        type=np.float64,
        unit='mA*hour/g',
        description="The charge a battery can deliver at the rated voltage, per unit mass."
    )

    voltage = Quantity(
        type=np.float64,
        unit='V',
        description="The electrical potential difference between the battery terminals."
    )

    coulombic_efficiency = Quantity(
        type=np.float64,
        unit='',
        description="The ratio of charge extracted from the battery to charge input per cycle."
    )

    energy_density = Quantity(
        type=np.float64,
        unit='W*hour/kg',
        description="The amount of energy stored per unit mass."
    )

    conductivity = Quantity(
        type=np.float64,
        unit='S/m',
        description="The ability of a battery material to conduct electric current."
    )

    DOI = Quantity(
        type=str,
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
        description="DOI reference for the source publication."
    )

    journal = Quantity(
        type=str,
        description="Journal where the research was published."
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        super().normalize(archive, logger)

class BatteryDatabase(Schema):
    m_def = Section(
        label='Battery database',
        extends=['nomad.datamodel.data.EntryData'],  # makes it valid for archive.data
    )
    batteries = SubSection(sub_section=BatteryProperties, repeats=True)
    
m_package.__init_metainfo__()