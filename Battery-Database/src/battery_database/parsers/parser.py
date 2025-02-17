import pandas as pd
from typing import TYPE_CHECKING
from schema_packages.schema_package import BatteryProperties

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import EntryArchive
    from structlog.stdlib import BoundLogger

from nomad.config import config
from nomad.parsing.parser import MatchingParser

configuration = config.get_plugin_entry_point(
    'battery_database.parsers:parser_entry_point'
)


class BatteryParser(MatchingParser):
    def parse(
        self,
        mainfile: str,
        archive: 'EntryArchive',
        logger: 'BoundLogger',
        child_archives: dict[str, 'EntryArchive'] = None,
    ) -> None:
        logger.info('BatteryParser.parse', parameter=configuration.parameter)

        # Read CSV file
        try:
            df = pd.read_csv(mainfile)
        except Exception as e:
            logger.error(f"Failed to read CSV file: {e}")
            return

        # Iterate over rows and create a BatteryProperties section
        for _, row in df.iterrows():
            battery_entry = archive.m_create(BatteryProperties)

            # Assign extracted values, handling missing data
            battery_entry.material_name = row.get("Name", "Unknown Material")
            battery_entry.capacity = float(row.get("Value", 0)) if row.get("Property") == "Capacity" else None
            battery_entry.voltage = float(row.get("Value", 0)) if row.get("Property") == "Voltage" else None
            battery_entry.coulombic_efficiency = float(row.get("Value", 0)) if row.get("Property") == "Coulombic Efficiency" else None
            battery_entry.energy_density = float(row.get("Value", 0)) if row.get("Property") == "Energy Density" else None
            battery_entry.conductivity = float(row.get("Value", 0)) if row.get("Property") == "Conductivity" else None
            battery_entry.DOI = row.get("DOI", "No DOI Available")
            battery_entry.journal = row.get("Journal", "Unknown Journal")

            # Log the extracted data
            logger.info(f"Parsed entry: {battery_entry.material_name}, {battery_entry.capacity}, {battery_entry.voltage}")