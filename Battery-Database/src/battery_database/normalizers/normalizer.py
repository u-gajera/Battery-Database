from typing import TYPE_CHECKING
import numpy as np
from battery_database.schema_packages.schema_package import BatteryProperties

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import EntryArchive
    from structlog.stdlib import BoundLogger

from nomad.config import config
from nomad.normalizing import Normalizer

#configuration = config.get_plugin_entry_point('schema_package_entry_point')
configuration = None
if hasattr(config, "get_plugin_entry_point") and callable(config.get_plugin_entry_point):
    configuration = config.get_plugin_entry_point('schema_package_entry_point')

class BatteryNormalizer(Normalizer):
    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        super().normalize(archive, logger)
        logger.info('BatteryNormalizer.normalize', parameter=configuration.parameter)

        battery_data = archive.section(BatteryProperties)

        if battery_data is not None:
            # missing values
            if not battery_data.material_name or battery_data.material_name.strip() == "":
                battery_data.material_name = "Unknown Material"

            if not battery_data.DOI or battery_data.DOI.strip() == "":
                battery_data.DOI = "No DOI Available"

            if not battery_data.journal or battery_data.journal.strip() == "":
                battery_data.journal = "Unknown Journal"

            battery_data.capacity = np.nan if not battery_data.capacity or battery_data.capacity == "" else battery_data.capacity
            battery_data.voltage = np.nan if not battery_data.voltage or battery_data.voltage == "" else battery_data.voltage
            battery_data.coulombic_efficiency = np.nan if not battery_data.coulombic_efficiency or battery_data.coulombic_efficiency == "" else battery_data.coulombic_efficiency
            battery_data.energy_density = np.nan if not battery_data.energy_density or battery_data.energy_density == "" else battery_data.energy_density
            battery_data.conductivity = np.nan if not battery_data.conductivity or battery_data.conductivity == "" else battery_data.conductivity

