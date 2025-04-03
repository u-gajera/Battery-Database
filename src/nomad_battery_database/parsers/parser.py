import pandas as pd
from typing import TYPE_CHECKING
#from schema_packages.schema_package import BatteryProperties
from nomad_battery_database.schema_packages.schema_package import BatteryProperties

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import EntryArchive
    from structlog.stdlib import BoundLogger

from nomad.config import config
from nomad.parsing.parser import MatchingParser


class BatteryParser(MatchingParser):
    def parse(
        self,
        mainfile: str,
        archive: 'EntryArchive',
        logger: 'BoundLogger',
        child_archives: dict[str, 'EntryArchive'] = None,
    ) -> None:
        # reading CSV file
        try:
            df = pd.read_csv(mainfile)
        except Exception as e:
            logger.error(f"Failed to read CSV file: {e}")
            return

        # dictionary to store material data
        battery_data = {}

        # iterate over rows and create BatteryProperties sections
        for _, row in df.iterrows():
            material_name = row.get("Name", "Unknown Material")
            property_type = row.get("Property")
            value = row.get("Value")
            doi = row.get("DOI", "No DOI Available")
            journal = row.get("Journal", "Unknown Journal")

            # check material entry if not exists
            if material_name not in battery_data:
                battery_data[material_name] = archive.m_create(BatteryProperties)
                battery_data[material_name].material_name = material_name
                battery_data[material_name].DOI = doi
                battery_data[material_name].journal = journal
                #print(battery_data[material_name].material_name)

            # check extracted values based on property type
            if property_type == "Capacity":
                battery_data[material_name].capacity = float(value) if pd.notna(value) else None
            elif property_type == "Voltage":
                battery_data[material_name].voltage = float(value) if pd.notna(value) else None
            elif property_type == "Coulombic Efficiency":
                battery_data[material_name].coulombic_efficiency = float(value) if pd.notna(value) else None
            elif property_type == "Energy Density":
                battery_data[material_name].energy_density = float(value) if pd.notna(value) else None
                #print(battery_data[material_name].energy_density)
            elif property_type == "Conductivity":
                battery_data[material_name].conductivity = float(value) if pd.notna(value) else None

        # log the parsed data
        for material, entry in battery_data.items():
            logger.info(f"Parsed entry: {material}, {entry.capacity}, {entry.voltage}")
