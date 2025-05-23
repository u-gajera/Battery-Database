# -*- -*-
from __future__ import annotations

from nomad.config.models.plugins import AppEntryPoint
from nomad.config.models.ui import (
    App,
    Column,
    Dashboard,
    Layout,
    SearchQuantities,
    WidgetPeriodicTable,
)

# Fully‑qualified name of the schema we want to expose in the UI.
SCHEMA = "nomad_battery_database.schema_packages.battery_schema.BatteryProperties"

battery_app = AppEntryPoint(
    name="battery_app",
    description="Explore Properties from single-file YAML uploads.",
    app=App(
        # ------------------------------------------------ overview ----------
        label="Curated Battery Database",
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
            "section_defs.definition_qualified_name": [SCHEMA], 
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
                selected=True, 
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
