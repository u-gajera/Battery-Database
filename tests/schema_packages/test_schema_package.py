import os

from nomad.client import normalize_all, parse
from nomad.datamodel import EntryArchive, EntryMetadata

from nomad_battery_database.schema_packages.battery_schema import (
    ChemDataExtractorBattery,
)

CREATE_ARCHIVE_TARGET = 'nomad_battery_database.parsers.battery_parser.create_archive'
EXPECTED_ARCHIVE_COUNT = 85


def test_schema_package_with_monkeypatch(monkeypatch):
    csv_file = os.path.join(
        'tests', 'data', 'battery_data_pivot.extracted_battery.csv'
    )
    assert os.path.exists(csv_file), (
        f'Test file not found at {csv_file}. '
        'Ensure the path is correct relative to where you run pytest.'
    )
    captured_archives = []
    def mock_create_archive(db_section, parent_archive, file_name):
        metadata = EntryMetadata(entry_name=file_name)
        new_archive = EntryArchive(data=db_section, metadata=metadata)
        captured_archives.append(new_archive)
    monkeypatch.setattr(CREATE_ARCHIVE_TARGET, mock_create_archive)
    parse(csv_file)

    captured_count = len(captured_archives)
    assert captured_count == EXPECTED_ARCHIVE_COUNT, (
        f'Expected {EXPECTED_ARCHIVE_COUNT} archives for {EXPECTED_ARCHIVE_COUNT} '
        f'rows, but captured {captured_count}.'
    )
    print(f'\nSuccessfully captured {captured_count} archives.')

    for i, entry_archive in enumerate(captured_archives):
        normalize_all(entry_archive)

        battery_section = entry_archive.data
        assert battery_section is not None, f'Archive #{i} is missing a data section.'

        assert isinstance(battery_section, ChemDataExtractorBattery), (
            f'Archive #{i} data is not a ChemDataExtractorBattery instance.'
        )
        if getattr(entry_archive.results, "material", None) is None:
            print(f"⚠️ Warning: Archive #{i} is missing results.material.")

        assert entry_archive.results is not None, f'Archive #{i} is missing results.'
        # assert entry_archive.results.material is not None, (
        #     f'Archive #{i} is missing results.material.'
        # )
        assert entry_archive.results.material.chemical_formula_hill is not None, (
            f'Archive #{i} failed to normalize chemical_formula_hill.'
        )

    print(f'All {captured_count} archives passed general checks after normalization.')

    first_archive = captured_archives[0]
    first_section = first_archive.data
    assert first_section.material_name == '40-CuO / C'
    assert first_section.doi == '10.1039/C4NR06432A'
    assert first_archive.results.material.chemical_formula_hill == 'CCuO'
    print('Detailed spot-check on the first entry passed.')

    lco_archive = None
    for arch in captured_archives:
        if arch.data.material_name == 'LCO':
            lco_archive = arch
            break
    
    assert lco_archive is not None, "Could not find the 'LCO' entry to test."
    assert lco_archive.results.material.elements == ['Co', 'Li', 'O']
    assert lco_archive.data.coulombic_efficiency is not None
    print("Detailed spot-check on 'LCO' entry passed.")