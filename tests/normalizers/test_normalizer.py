import os
import pytest
import logging
import numpy as np
from nomad.datamodel import EntryArchive
from src.nomad_battery_database.parsers.parser import BatteryParser
from src.nomad_battery_database.normalizers.normalizer import BatteryNormalizer

# Define test file path
TEST_FILE_PATH = os.path.join(os.path.dirname(__file__), "../data/test_battery_data.csv")

@pytest.fixture
def archive():
    return EntryArchive()

def test_normalizer(archive):
    parser = BatteryParser()
    normalizer = BatteryNormalizer()

    # Ensure test file exists
    assert os.path.exists(TEST_FILE_PATH), f"Test file {TEST_FILE_PATH} not found."

    # Run parser
    parser.parse(mainfile=TEST_FILE_PATH, archive=archive, logger=logging.getLogger())

    # Run normalizer
    normalizer.normalize(archive=archive, logger=logging.getLogger())

    first_entry = archive.section_metadata[0]
    
    # Check normalization - np.nan for missing values
    assert first_entry.material_name != "", "Material name is missing"
    assert np.isnan(first_entry.capacity) == False, "Capacity should not be NaN"
    assert np.isnan(first_entry.voltage) == False, "Voltage should not be NaN"
    assert np.isnan(first_entry.coulombic_efficiency) == True, "Coulombic Efficiency should be NaN (missing)"

