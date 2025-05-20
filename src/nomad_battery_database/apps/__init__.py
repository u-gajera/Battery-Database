"""
Battery-database GUI app (YAML uploads).

[project.entry-points."nomad.plugin"]
battery_app = "nomad_battery_database.apps:battery_app"
"""

from nomad.config.models.plugins import AppEntryPoint
from nomad.config.models.ui import (
    App,
    Column,
    Menu,
    MenuItemHistogram,
    MenuItemPeriodicTable,
    MenuItemTerms,
    SearchQuantities,
)

# fully-qualified name of the schema section
SCHEMA = "nomad_battery_database.schema_packages.battery.BatteryProperties"

battery_app = AppEntryPoint(
    name="battery_app",
    description="Explore capacity, voltage, CE, … extracted from single-file YAML uploads.",
    app=App(
        # ------------------------------------------------ overview ----------
        label="Battery Database",
        path="batterydb",
        category="Experiments",
        description="Curated electro-chemical properties from the literature.",
        readme=("Uploads are single YAML files parsed by the battery-database "
                "plugin.  Use the filters on the left or the search bar on top."),

        # -------------------------------- search index ----------------------
        search_quantities=SearchQuantities(
            include=[f"*#{SCHEMA}"],   # load *all* scalar quantities in one go
        ),

        # -------------------------------- fixed filters ---------------------
        filters_locked={
            "section_defs.definition_qualified_name": [SCHEMA],
            # uncomment to ignore legacy CSV uploads
            # "mainfile~": [".yaml$", ".yml$"],
        },

        # -------------------------------- result table ----------------------
        columns=[
            Column(
                quantity=f"data.Material_entries[*].material_name#{SCHEMA}",
                label="Material",
                selected=True,
            ),
            Column(
                quantity=f"data.Material_entries[*].capacity#{SCHEMA}",
                label="Capacity (mAh g⁻¹)",
                selected=True,
            ),
            Column(
                quantity=f"data.Material_entries[*].voltage#{SCHEMA}",
                label="Voltage (V)",
                selected=True,
            ),
            Column(
                quantity=f"data.Material_entries[*].coulombic_efficiency#{SCHEMA}",
                label="CE (%)",
            ),
            Column(quantity="entry_id", label="Entry ID"),
            Column(quantity="upload_create_time", label="Upload time"),
        ],

        # -------------------------------- left-hand menu --------------------
        menu=Menu(
            title="Battery filters",
            items=[
                Menu(
                    title="Material",
                    items=[
                        MenuItemPeriodicTable(
                            search_quantity="results.material.elements",
                        ),
                        MenuItemTerms(
                            quantity="results.material.chemical_formula_hill",
                            width=6,
                            options=0,
                        ),
                    ],
                ),
                Menu(
                    title="Properties",
                    items=[
                        MenuItemHistogram(
                            x=f"data.Material_entries[*].capacity#{SCHEMA}",
                            width=12,
                            show_statistics=True,
                        ),
                        MenuItemHistogram(
                            x=f"data.Material_entries[*].voltage#{SCHEMA}",
                            width=12,
                            show_statistics=True,
                        ),
                    ],
                ),
            ],
        ),
    ),
)

__all__ = ["battery_app"]
