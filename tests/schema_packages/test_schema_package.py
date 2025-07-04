import os

from nomad.client import normalize_all, parse
from nomad_battery_database.schema_packages.schema_package import BatteryProperties


def test_schema_package():
    # Define test file path
    test_file = os.path.join('tests', 'data', 'test_battery_data.csv')

    # Ensure test file exists
    assert os.path.exists(test_file), f"Test file {test_file} not found."

    # Create a mock archive and normalize
    entry_archive = parse(test_file)[0]
    normalize_all(entry_archive)

    # Check if schema was applied correctly
    battery_section = entry_archive.section(BatteryProperties)

    # Check if it's an instance of BatteryProperties
    is_valid = isinstance(battery_section, BatteryProperties)

    # Assert with a clear error message if not valid
    assert is_valid, "Schema not applied correctly"

