"""
Battery-database GUI app (YAML uploads).

[project.entry-points."nomad.plugin"]
battery_app = "nomad_battery_database.apps:battery_app"
"""

from nomad.config.models.plugins import AppEntryPoint
from nomad.config.models.ui import (
    App,
    Column,
    Menu, # Ensure Menu is imported
    MenuItemHistogram, # Ensure MenuItemHistogram is imported
    MenuItemPeriodicTable, # Ensure MenuItemPeriodicTable is imported
    MenuItemTerms, # Ensure MenuItemTerms is imported
    SearchQuantities,
    Dashboard,
    WidgetPeriodicTable,
    Layout,
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
        description="Curated electro-chemical battery properties from the literature.",
        readme=("Uploads are single YAML files parsed by the battery-database "
                "plugin.  Use the filters on the left or the search bar on top."),

        # -------------------------------- searching index ----------------------
        # load *all* quantities from BatteryProperties (including 'elements')
        search_quantities=SearchQuantities(
            include=[
                f"*#{SCHEMA}",
                f"data.Material_entries.elements#{SCHEMA}",
            ],
        ),

        # -------------------------------- fixed filters ---------------------
        filters_locked={
            "section_defs.definition_qualified_name": [SCHEMA], # Focus on entries with BatteryProperties
            # "mainfile~": [".yaml$", ".yml$"], # You might want to enable this if only YAMLs are expected
        },

        # -------------------------------- result table ----------------------
        columns=[
            Column(
                quantity=f"data.Material_entries[*].material_name#{SCHEMA}",
                label="Material",
                selected=True,
            ),
            Column( # Added 'elements' column for display, optional
                quantity=f"data.Material_entries[*].elements#{SCHEMA}",
                label="Elements",
                selected=False, # Default to not shown, user can enable
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
            Column(
                quantity=f"data.Material_entries[*].chemical_formula_hill#{SCHEMA}",
                label="Formula (Hill)",
                selected=True, # Make it selected by default as it's useful
            ),
            Column(quantity="entry_id", label="Entry ID"),
            Column(quantity="upload_create_time", label="Upload time"),
        ],

        # -------------------------------- left-hand menu --------------------
        # menu = Menu(
        #     title="Filters & Metrics",
        #     items=[
        #         MenuItemPeriodicTable(
        #             label="Elements",
        #             search_quantity=f"data.Material_entries.elements#{SCHEMA}",
        #             description="Filter materials containing selected elements",
        #             width=12,
        #         ),
        #     ],
        # ),
        dashboard = Dashboard(
            widgets=[
                WidgetPeriodicTable(
                    title="Elements present in selected entries",
                    search_quantity=f"data.Material_entries.elements#{SCHEMA}",
                    layout={'lg': Layout(w=12, h=8, x=0, y=0, minW=12, minH=8)},
                    show_statistics=True,
                ),
            ],
        )
    ),
)

__all__ = ["battery_app"]
