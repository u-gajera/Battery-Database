from typing import TYPE_CHECKING

import pandas as pd
from nomad.parsing.parser import MatchingParser

from nomad_battery_database.schema_packages.schema_package import (
    BatteryDatabase,
    BatteryProperties,
)

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import EntryArchive
    from structlog.stdlib import BoundLogger

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

        archive.data = BatteryDatabase()
        # dictionary to store material data

        def _to_float(x):
            # return None for Nan values
            return float(x) if pd.notna(x) else None
        
        # iterate over rows and create BatteryProperties sections
        for _, row in df.iterrows():
            material_name = row.get("Name", "Unknown Material")

            # create a fresh BatteryProperties section for each row
            entry = archive.data.m_create(BatteryProperties) 
            entry.material_name = material_name
            entry.DOI           = row.get("DOI", "No DOI Available")
            entry.journal       = row.get("Journal", "Unknown Journal")

            # numeric properties (column names as in the pivoted CSV)
            entry.capacity              = _to_float(row.get("Capacity_Value"))
            entry.voltage               = _to_float(row.get("Voltage_Value"))
            entry.coulombic_efficiency  = _to_float(row.get("Coulombic_Efficiency"))
            entry.energy_density        = _to_float(row.get("Energy_Density"))
            entry.conductivity          = _to_float(row.get("Conductivity"))

            #battery_data[material_name] = entry
            logger.info(
                f"Parsed entry: {material_name}, "
                f"capacity={entry.capacity}, voltage={entry.voltage}"
            )
