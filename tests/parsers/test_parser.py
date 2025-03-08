import os
import pytest
import logging
from nomad.datamodel import EntryArchive
from nomad_battery_database.schema_packages.schema_package import BatteryProperties

# Define test file path
TEST_FILE_PATH = os.path.join(os.path.dirname(__file__), "../data/test_battery_data.csv")

@pytest.fixture
def archive():
    return EntryArchive()

def test_parser(archive):
    parser = BatteryParser()

    # Ensure test file exists
    assert os.path.exists(TEST_FILE_PATH), f"Test file {TEST_FILE_PATH} not found."

    # Run parser
    parser.parse(mainfile=TEST_FILE_PATH, archive=archive, logger=logging.getLogger())

    # Assertions to validate parsing
    assert len(archive.section_metadata) > 0, "Parser did not extract any data."

    first_entry = archive.section_metadata[0]
    assert first_entry.material_name == "Material A"
    assert first_entry.capacity == 150.0
    assert first_entry.voltage == 3.7

