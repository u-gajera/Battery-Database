#import ast  # Ensure ast is imported
import ast
from typing import TYPE_CHECKING

import numpy as np
from nomad.datamodel.data import Schema
from nomad.datamodel.metainfo.annotations import ELNAnnotation, ELNComponentEnum
from nomad.metainfo import Quantity, SchemaPackage, Section, SubSection

if TYPE_CHECKING:  # pragma: no cover
    from nomad.datamodel import EntryArchive
    from structlog.stdlib import BoundLogger

m_package = SchemaPackage()

class BatteryProperties(Schema):
    """ Metadata extracted from **one** publication / **one** material."""

    # bibliographic
    material_name = Quantity(type=str, 
                    a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity))
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
        description='A list of unique chemical elements present in the material, ' \
                    'derived from extracted_name.',
        a_eln=ELNAnnotation(label='Elements Present')
    )

    def _parse_elements(self, raw, entry_log_prefix, logger) -> list[str] | None:
        """
        Extract a list of unique element symbols from extracted_name.
        Expects a stringified list of dicts or a list of dicts.
        """
        if not raw:
            return None

        try:
            if isinstance(raw, str):
                parts = ast.literal_eval(raw)
            elif isinstance(raw, list):
                parts = raw
            else:
                return None

            totals = {}
            for part in parts:
                if isinstance(part, dict):
                    for elem in part:
                        totals[elem] = totals.get(elem, 0) + 1

            return sorted(totals)
        except Exception as e:
            logger.warning(
                f"{entry_log_prefix}Failed to parse elements from extracted_name: {e}"
            )
            return None

    def normalize(
        self,
        archive: "EntryArchive",
        logger: "BoundLogger",
    ) -> None:  # noqa: D401
        super().normalize(archive, logger)

        # Build a short prefix once, then reuse it.
        entry_id = archive.metadata.entry_id if archive.metadata else "N/A"
        entry_log_prefix = f"[EntryID: {entry_id}] "

        logger.info(
            f"{entry_log_prefix}Starting normalization of BatteryProperties. "
            f"Initial extracted_name: '{self.extracted_name}', "
            f"type: {type(self.extracted_name)}"
        )

        # 1) Parse elements from extracted_name in one helper 
        self.elements = self._parse_elements(self.extracted_name, 
                                             entry_log_prefix, 
                                             logger) or []

        # 2) Bulk-assign all “_raw_value” → clean fields
        for raw, clean in [
            ("capacity_raw_value", "capacity"),
            ("voltage_raw_value", "voltage"),
            ("coulombic_efficiency_raw_value", "coulombic_efficiency"),
            ("energy_density_raw_value", "energy_density"),
            ("conductivity_raw_value", "conductivity"),
        ]:
            val = getattr(self, raw, None)
            if val is not None:
                setattr(self, clean, val)

        # 3) If you have “_raw_unit” fields, assign those too
        for raw_u, clean in [
            ("capacity_raw_unit", "capacity"),
            ("voltage_raw_unit", "voltage"),
            ("energy_density_raw_unit", "energy_density"),
            ("conductivity_raw_unit", "conductivity"),
        ]:
            unit = getattr(self, raw_u, None)
            if unit and getattr(self, clean, None) is not None:
                getattr(self, clean).unit = unit

        logger.info(f"{entry_log_prefix}Finished normalization of BatteryProperties.")

class BatteryDatabase(Schema):
    m_def = Section(label="Battery database", 
                    extends=["nomad.datamodel.data.EntryData"])
    Material_entries = SubSection(sub_section=BatteryProperties, 
                                  repeats=True)

m_package.__init_metainfo__()

__all__ = ["m_package", 
           "BatteryProperties", 
           "BatteryDatabase"]
