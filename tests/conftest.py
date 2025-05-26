# "function"	New instance for every test function
# "class"	One instance per test class
# "module"	One instance per test file (.py module)
# "session"	One instance for the entire test run

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

# Repository‑relative paths – resolved once per session

ROOT_DIR = Path(__file__).resolve().parents[1]          # repo root (…/project)
SRC_DIR = ROOT_DIR / "src"                               # project source tree
DATA_DIR = Path(__file__).parent / "data"               # tests/data
YAML_ROWS_DIR = DATA_DIR / "yaml_rows"                  # tests/data/yaml_rows


# Make package importable even if **not** installed (helpful for fresh CI runs)
if SRC_DIR.exists() and str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


# Session‑scoped path fixtures

@pytest.fixture(scope="session")
def project_root() -> Path:
    """Absolute path to the repository root."""
    return ROOT_DIR


@pytest.fixture(scope="session")
def src_dir() -> Path:
    """Absolute path to the ``src`` directory containing the package."""
    return SRC_DIR


@pytest.fixture(scope="session")
def data_dir() -> Path:
    """Absolute path to ``tests/data`` that holds sample files."""
    return DATA_DIR


@pytest.fixture(scope="session")
def yaml_rows_dir() -> Path:
    """Path to ``tests/data/yaml_rows`` (skips tests if the dir is missing)."""
    if not YAML_ROWS_DIR.exists():
        pytest.skip("yaml_rows directory not present – skipping related tests")
    return YAML_ROWS_DIR



# File‑list fixtures (session scope because data are read‑only)

@pytest.fixture(scope="session")
def yaml_files(data_dir: Path) -> list[Path]:
    """List of YAML files directly inside ``tests/data`` (not recursive)."""
    return sorted(data_dir.glob("*.yaml"))


@pytest.fixture(scope="session")
def yaml_row_files(yaml_rows_dir: Path) -> list[Path]:
    """List of YAML files inside the ``yaml_rows`` sub‑folder."""
    return sorted(yaml_rows_dir.glob("*.yaml"))


@pytest.fixture(scope="session")
def all_yaml_files(yaml_files: list[Path], yaml_row_files: list[Path]) -> list[Path]:
    """Combined list of *all* YAML files shipped with the test suite."""
    return yaml_files + yaml_row_files


@pytest.fixture(scope="session")
def csv_files(data_dir: Path) -> list[Path]:
    """List of CSV example files inside ``tests/data``."""
    return sorted(data_dir.glob("*.csv"))



# Battery‑database specific helpers

@pytest.fixture(scope="session")
def battery_parser_cls():
    """Import and return the :class:`BatteryParser` class."""
    from nomad_battery_database.parsers.battery_parser import BatteryParser
    return BatteryParser


@pytest.fixture(scope="function")
def fresh_parser(battery_parser_cls):
    """A *new* :class:`BatteryParser` instance for each test function."""
    return battery_parser_cls()


@pytest.fixture(scope="session")
def schema_modules():
    """Dictionary with imported schema modules used across tests."""
    battery_schema = importlib.import_module(
        "nomad_battery_database.schema_packages.battery_schema"
    )
    return {"battery_schema": battery_schema}

# testing new files
# def test_row_yaml_parse(fresh_parser, yaml_row_files):
#     for file in yaml_row_files:
#         archive = EntryArchive()
#         fresh_parser.parse(str(file), archive)
#         assert archive.data.Material_entries, f"{file.name} gave no entries"