# working fine for the csv parsing
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
    name = "battery_csv_parser"
    code_name = "battery-csv"
    domain = "battery-database"
    # ----------------------- extra helpers ----
    @staticmethod
    def _to_float(v):
        try:
            return float(v) if pd.notna(v) else None
        except Exception:
            return None

    @staticmethod
    def _to_str(v):
        return str(v) if pd.notna(v) else None

    # ------------------ main parse ------------
    def parse(
        self,
        mainfile: str,
        archive: "EntryArchive",
        logger: "BoundLogger",
        child_archives: dict[str, "EntryArchive"] | None = None,
    ) -> None:
        try:
            df = pd.read_csv(mainfile)
        except Exception as exc:
            logger.error("Failed to read CSV file", exc_info=exc)
            return

        archive.data = BatteryDatabase()

        property_map = {
            "Capacity": "capacity",
            "Conductivity": "conductivity",
            "Coulombic Efficiency": "coulombic_efficiency",
            "Energy Density": "energy_density",
            "Voltage": "voltage",
        }

        for _, row in df.iterrows():
            section: BatteryProperties = archive.data.m_create(BatteryProperties)

            # ---job identifiers ---
            section.material_name = self._to_str(row.get("Name"))
            section.extracted_name = self._to_str(row.get("Extracted_name"))

            # --- bibliographic ---
            section.title = self._to_str(row.get("Title"))
            section.DOI = self._to_str(row.get("DOI"))
            section.journal = self._to_str(row.get("Journal"))
            section.date = self._to_str(row.get("Date"))

            # --- extraction meta ---
            section.specifier = self._to_str(row.get("Specifier"))
            section.tag = self._to_str(row.get("Tag"))
            section.warning = self._to_str(row.get("Warning"))
            section.material_type = self._to_str(row.get("Type"))
            section.info = self._to_str(row.get("Info"))
            section.correctness = self._to_str(row.get("Correctness"))

            # --- electro‑chemical properties ---
            for csv_label, attr_base in property_map.items():
                # column names
                raw_unit_col = f"{csv_label}_Raw_unit"
                raw_value_col = f"{csv_label}_Raw_value"
                unit_col = f"{csv_label}_Unit"
                value_col = f"{csv_label}_Value"

                # fetching values
                raw_unit_val = self._to_str(row.get(raw_unit_col))
                raw_value_val = self._to_float(row.get(raw_value_col))
                unit_val = self._to_str(row.get(unit_col))
                value_val = self._to_float(row.get(value_col))

                setattr(section, f"{attr_base}_raw_unit", raw_unit_val)
                setattr(section, f"{attr_base}_raw_value", raw_value_val)
                setattr(section, f"{attr_base}_unit", unit_val)
                setattr(section, f"{attr_base}_value", value_val)

                # legacy aliases
                if attr_base == "capacity":
                    section.capacity = value_val
                elif attr_base == "conductivity":
                    section.conductivity = value_val
                elif attr_base == "coulombic_efficiency":
                    section.coulombic_efficiency = value_val
                elif attr_base == "energy_density":
                    section.energy_density = value_val
                elif attr_base == "voltage":
                    section.voltage = value_val

            logger.info("Parsed entry", material=section.material_name, doi=section.DOI)