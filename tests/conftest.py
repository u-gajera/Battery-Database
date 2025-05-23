import nomad
import pytest
from nomad.config.models.config import Plugins

# import your plugin entry points
from nomad_battery_database import battery_app
from nomad_battery_database.parsers import battery_parser
from nomad_battery_database.schema_packages.battery_schema import m_package


@pytest.fixture(autouse=True)
def init_nomad_plugins():
    """
    Initialize nomad.config.plugins with your battery-database plugin entry points
    so that pytest can discover and use them without ValidationError.
    """
    nomad.config.plugins = Plugins(
        entry_points=[
            battery_app,
            battery_parser,
            m_package,
        ],
        plugin_packages=["nomad_battery_database"],
    )
    yield