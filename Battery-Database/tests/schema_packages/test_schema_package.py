import os
import pytest
from nomad.client import normalize_all, parse
from battery_database.schema_packages.schema_package import BatteryProperties

def test_schema_package():
    # Define test file path
    test_file = os.path.join('tests', 'data', 'test_battery_data.csv')

    # Ensure test file exists
    assert os.path.exists(test_file), f"Test file {test_file} not found."

    # Create a mock archive and normalize
    entry_archive = parse(test_file)[0]
    normalize_all(entry_archive)

    # Check if schema was applied correctly
    assert isinstance(entry_archive.section(BatteryProperties), BatteryProperties), "Schema not applied correctly"

