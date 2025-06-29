from __future__ import annotations
from nomad.config.models.plugins import AppEntryPoint
from nomad.config.models.ui import (
    App,
    Axis,                 
    Column,
    Dashboard,
    Layout,
    Markers,              
    SearchQuantities,
    WidgetHistogram,
    WidgetPeriodicTable,
    WidgetScatterPlot,
    Menu,               
    MenuItemHistogram,  
    MenuItemTerms,
)

SCHEMA = "nomad_battery_database.schema_packages.battery_schema.BatteryDatabase"

battery_app = AppEntryPoint(
    name="battery_app",
    description="Explore Properties from single-file YAML uploads.",
    app=App(
        # ------------------------------------------------ overview ----------
        label="Curated Battery Database",
        path="batterydb",
        category="Experiments",
        description=(
            "Curated electro-chemical battery properties from the literature."
        ),
        readme=(
            "Uploads are single YAML files parsed by the battery-database "
            "plugin. Use the filters on the left or the search bar on top."
        ),

        # ---------------------------- search index -------------------------
        search_quantities=SearchQuantities(include=[f"*#{SCHEMA}"]),

        # ---------------------------- fixed filters ------------------------
        filters_locked={"section_defs.definition_qualified_name": [SCHEMA]},

        # ---------------------------- result table -------------------------
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
            Column(
                quantity=f"data.Material_entries[*].chemical_formula_hill#{SCHEMA}",
                label="Formula (Hill)",
                selected=True,
            ),
            Column(quantity="entry_id", label="Entry ID"),
            Column(quantity="upload_create_time", label="Upload time"),
        ],

        # ------------------------------ menu -----------------------------
        menu=Menu(
            title="Filters",
            items=[
                # categorical ­––––––––––––––––––––––––––––––––––––––––––––
                MenuItemTerms(
                    quantity=f"data.Material_entries.specifier#{SCHEMA}",
                    title="Specifier",          # e.g. anode / cathode / electrolyte
                    show_input=True,
                ),
                MenuItemTerms(
                    quantity=f"data.Material_entries.material_type#{SCHEMA}",
                    title="Material type",
                    show_input=True,
                ),
                MenuItemTerms(
                    quantity=f"data.Material_entries.tag#{SCHEMA}",
                    title="Tag",
                    show_input=True,
                ),
                # numerical ­–––––––––––––––––––––––––––––––––––––––––––––––
                MenuItemHistogram(
                    x=Axis(
                        search_quantity=f"data.Material_entries.capacity#{SCHEMA}",
                        title="Capacity (mAh g⁻¹)",
                    ),
                ),
                MenuItemHistogram(
                    x=Axis(
                        search_quantity=f"data.Material_entries.voltage#{SCHEMA}",
                        title="Voltage (V)",
                    ),
                ),
            ],
        ),

        # ---------------------------- dashboard ----------------------------
        dashboard=Dashboard(
            widgets=[
                # --- periodic table (unchanged) ---
                WidgetPeriodicTable(
                    title="Elements present in selected entries",
                    search_quantity="results.material.elements",
                    layout={"lg": Layout(w=12, h=8, x=0, y=0, minW=12, minH=8)},
                    show_statistics=True,
                ),

                # --- histograms ------------------------------------------------
                WidgetHistogram(  # Capacity )
                    title="Capacity distribution",
                    x=f"data.Material_entries.capacity#{SCHEMA}",
                    n_bins=100,
                    autorange=True,
                    layout={"lg": Layout(w=6, h=8, x=0, y=8, minW=6, minH=6)},
                ),
                WidgetHistogram(  # Voltage
                    title="Voltage distribution",
                    x=f"data.Material_entries.voltage#{SCHEMA}",
                    n_bins=100,
                    autorange=True,
                    layout={"lg": Layout(w=6, h=6, x=0, y=16, minW=6, minH=6)},
                ),
                WidgetHistogram(  # Coulombic Efficiency
                    title="CE distribution",
                    x=f"data.Material_entries.coulombic_efficiency#{SCHEMA}",
                    n_bins=100,
                    autorange=True,
                    layout={"lg": Layout(w=6, h=6, x=6, y=16, minW=6, minH=6)},
                ),
                WidgetHistogram(  # Conductivity
                    title="Conductivity distribution",
                    x=f"data.Material_entries.conductivity#{SCHEMA}",
                    n_bins=100,
                    autorange=True,
                    layout={"lg": Layout(w=6, h=6, x=0, y=22, minW=6, minH=6)},
                ),
                WidgetHistogram(  # Energy density
                    title="Energy-density distribution",
                    x=f"data.Material_entries.energy_density#{SCHEMA}",
                    n_bins=100,
                    autorange=True,
                    layout={"lg": Layout(w=6, h=6, x=6, y=22, minW=6, minH=6)},
                ),

                # --- scatter plot (Voltage vs Capacity coloured by Specifier) --
                WidgetScatterPlot(
                    title="Voltage vs Capacity (by Specifier)",
                    x=Axis(
                        search_quantity=f"data.Material_entries[*].voltage#{SCHEMA}",
                        title="Voltage (V)",
                    ),
                    y=Axis(
                        search_quantity=f"data.Material_entries[*].capacity#{SCHEMA}",
                        title="Capacity (mAh g⁻¹)",
                    ),
                    markers=Markers(
                        color=Axis(
                            search_quantity=f"data.Material_entries[*].specifier#{SCHEMA}",
                            title="Specifier",
                        )
                    ),
                    size=800,
                    autorange=True,
                    layout={"lg": Layout(w=6, h=8, x=6, y=8, minW=6, minH=6)},
                ),
            ],
        ),
    ),
)

__all__ = ["battery_app"]
