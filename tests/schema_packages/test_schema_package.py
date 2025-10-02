import os

import pytest
from nomad.client import normalize_all, parse
from nomad.datamodel import EntryArchive, EntryMetadata

from nomad_battery_database.schema_packages.battery_schema import (
    ChemDataExtractorBattery,
)

# Define constants for test configuration
CREATE_ARCHIVE_TARGET = 'nomad_battery_database.parsers.battery_parser.create_archive'
EXPECTED_ARCHIVE_COUNT = 85
TEST_CSV_FILE = os.path.join(
    'tests', 'data', 'battery_data_pivot.extracted_battery.csv'
)


@pytest.fixture
def captured_archives(monkeypatch) -> list[EntryArchive]:
    """
    Parse the test CSV and capture the generated EntryArchive objects.

    This fixture uses monkeypatch to replace the real create_archive function
    with a mock that collects archives into a list.
    """
    if not os.path.exists(TEST_CSV_FILE):
        pytest.fail(f'Test data file not found at: {TEST_CSV_FILE}')

    archives = []

    def mock_create_archive(db_section, parent_archive, file_name):
        """A mock function to capture archives instead of writing them."""
        metadata = EntryMetadata(entry_name=file_name)
        new_archive = EntryArchive(data=db_section, metadata=metadata)
        archives.append(new_archive)

    monkeypatch.setattr(CREATE_ARCHIVE_TARGET, mock_create_archive)

    parse(TEST_CSV_FILE)
    return archives


def test_archive_creation_and_count(captured_archives):
    """Test if the correct number of archives were created by the parser."""
    captured_count = len(captured_archives)
    assert captured_count == EXPECTED_ARCHIVE_COUNT, (
        f'Expected {EXPECTED_ARCHIVE_COUNT} archives, but got {captured_count}.'
    )
    print(f'Successfully captured {captured_count} archives.')


def test_archive_normalization_and_structure(captured_archives):
    """
    Test if all captured archives normalize successfully and check their basic
    structure and content.
    """
    for i, entry_archive in enumerate(captured_archives):
        material_name = getattr(entry_archive.data, 'material_name', 'Unknown')
        print(f'Checking archive #{i} ({material_name})...')

        try:
            normalize_all(entry_archive)
        except Exception as e:
            msg = (
                f'Normalization failed for archive #{i} ({material_name}) with '
                f'error: {e}. This often points to a schema definition issue.'
            )
            pytest.fail(msg)

        # General health checks for each archive
        assert entry_archive.data is not None, f'Archive #{i} is missing data.'
        assert isinstance(entry_archive.data, ChemDataExtractorBattery), (
            f'Archive #{i} data is not a {ChemDataExtractorBattery.__name__}.'
        )
        assert entry_archive.data.material_name is not None, (
            f'Archive #{i} is missing a material_name.'
        )

        # Check that results are populated after normalization
        assert entry_archive.results is not None, f'Archive #{i} is missing results.'
        assert entry_archive.results.material is not None, (
            f'Archive #{i} failed to populate results.material.'
        )
        assert entry_archive.results.material.chemical_formula_hill is not None, (
            f'Archive #{i} is missing the Hill formula in results.material.'
        )

    print(
        f'All {len(captured_archives)} archives passed normalization and '
        'general health checks.'
    )


def test_specific_archive_content(captured_archives):
    """
    Perform detailed spot-checks on specific, known entries to ensure
    data is processed and normalized correctly.
    """
    # Normalize all archives first to ensure data is populated for checks
    for archive in captured_archives:
        normalize_all(archive)

    # --- Test 1: Detailed check on the first entry ---
    first_archive = captured_archives[0]
    first_section = first_archive.data
    first_material = first_archive.results.material

    assert first_section.material_name == '40-CuO / C'
    assert first_section.doi == '10.1039/C4NR06432A'

    expected_formula = 'C & CuO'
    actual_formula = first_material.chemical_formula_hill
    assert actual_formula == expected_formula, (
        f"Expected Hill formula '{expected_formula}' for first entry, "
        f"but got '{actual_formula}'."
    )
    print('Detailed spot-check on the first entry passed.')

    # --- Test 2: Find and test the "LCO" entry ---
    lco_archive = next(
        (arch for arch in captured_archives if arch.data.material_name == 'LCO'), None
    )
    assert lco_archive is not None, "Could not find the 'LCO' entry to test."

    lco_material = lco_archive.results.material
    expected_elements = sorted(['Co', 'Li', 'O'])
    actual_elements = sorted(lco_material.elements)
    assert actual_elements == expected_elements, (
        f'Incorrect elements for LCO entry. Expected {expected_elements}, '
        f'got {actual_elements}.'
    )
    assert lco_archive.data.coulombic_efficiency is not None
    print("Detailed spot-check on 'LCO' entry passed.")