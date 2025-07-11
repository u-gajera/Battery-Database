from __future__ import annotations

from nomad.config.models.plugins import AppEntryPoint
from nomad.config.models.ui import (
    App,
    Axis,
    Column,
    Dashboard,
    Layout,
    # Markers,
    Menu,
    MenuItemTerms,
    SearchQuantities,
    WidgetHistogram,
    WidgetPeriodicTable,
    WidgetScatterPlot,
)

SCHEMA = 'nomad_battery_database.schema_packages.battery_schema.BatteryDatabase'

battery_app = AppEntryPoint(
    name='battery_app',
    description='Explore Properties from single-file YAML uploads.',
    app=App(
        # ------------------------------------------------ overview ----------
        label='Curated Battery Database',
        path='batterydb',
        category='Experiments',
        description=('Curated Experimental Battery properties from the literature.'),
        readme=(
            'Uploads are single YAML files parsed by the battery-database '
            'plugin. Use the filters on the left or the search bar on top.'
        ),
        # ---------------------------- search index -------------------------
        search_quantities=SearchQuantities(include=[f'data.*#{SCHEMA}']),
        # ---------------------------- fixed filters ------------------------
        filters_locked={'section_defs.definition_qualified_name': [SCHEMA]},
        # ---------------------------- result table -------------------------
        columns=[
            Column(
                quantity=f'data.material_name#{SCHEMA}',
                label='Material',
                selected=True,
            ),
            Column(
                quantity=f'data.publication.journal#{SCHEMA}',
                label='Journal',
                selected=True,
            ),
            Column(
                quantity=f'data.publication_year#{SCHEMA}',
                label='Publication Year',
            ),
            Column(
                quantity=f'data.capacity#{SCHEMA}',
                label='Capacity',
                selected=True,
                unit='mA*hour/g',
            ),
            Column(
                quantity=f'data.voltage#{SCHEMA}',
                label='Open-circuit voltage',
                selected=True,
            ),
            Column(
                quantity=f'data.coulombic_efficiency#{SCHEMA}',
                label='Coulombic efficiency',
                selected=True,
            ),
            Column(
                quantity=f'data.energy_density#{SCHEMA}',
                label='Energy density',
                selected=True,
                unit='W*hour/kg',
            ),
            Column(
                quantity=f'data.conductivity#{SCHEMA}',
                label='Conductivity',
                selected=True,
            ),
            Column(
                quantity=f'data.chemical_formula_hill#{SCHEMA}',
                label='Formula (Hill)',
            ),
            Column(quantity='entry_id', label='Entry ID'),
            Column(quantity='upload_create_time', label='Upload time'),
        ],
        # ------------------------------ menu -----------------------------
        menu=Menu(
            title='Filters',
            items=[
                # categorical ­––––––––––––––––––––––––––––––––––––––––––––
                MenuItemTerms(
                    quantity=f'data.chemical_formula_hill#{SCHEMA}',
                    title='Material',
                    show_input=True,
                ),
                MenuItemTerms(
                    quantity=f'data.publication.journal#{SCHEMA}',
                    title='Journal',
                    show_input=True,
                ),
                # MenuItemTerms(
                #     # NOTE: this is not working
                #     quantity=f'data.publication.publication_date#{SCHEMA}',
                #     title='Publication Year',
                # ),
                MenuItemTerms(
                    quantity=f'data.specifier#{SCHEMA}',
                    title='Specifier',
                    show_input=True,
                ),
                MenuItemTerms(
                    quantity=f'data.tag#{SCHEMA}',
                    title='Tag',
                    show_input=True,
                ),
            ],
        ),
        # ---------------------------- dashboard ----------------------------
        dashboard=Dashboard(
            widgets=[
                # --- periodic table (unchanged) ---
                WidgetPeriodicTable(
                    title='Elements present in selected entries',
                    search_quantity='results.material.elements',
                    layout={'lg': Layout(w=12, h=8, x=0, y=0, minW=12, minH=8)},
                ),
                # --- histograms ------------------------------------------------
                WidgetHistogram(  # Capacity )
                    title='Capacity distribution',
                    x=f'data.capacity#{SCHEMA}',
                    n_bins=100,
                    autorange=True,
                    unit='mA*hour/g',
                    layout={'lg': Layout(w=6, h=8, x=0, y=8, minW=6, minH=6)},
                ),
                WidgetHistogram(  # Voltage
                    title='Voltage distribution',
                    x=f'data.voltage#{SCHEMA}',
                    n_bins=100,
                    autorange=True,
                    layout={'lg': Layout(w=6, h=8, x=6, y=8, minW=6, minH=6)},
                ),
                WidgetHistogram(  # Coulombic Efficiency
                    title='Coulombic Efficiency distribution',
                    x=f'data.coulombic_efficiency#{SCHEMA}',
                    n_bins=100,
                    autorange=True,
                    layout={'lg': Layout(w=6, h=8, x=12, y=8, minW=6, minH=6)},
                ),
                WidgetHistogram(  # Conductivity
                    title='Conductivity distribution',
                    x=f'data.conductivity#{SCHEMA}',
                    n_bins=100,
                    autorange=True,
                    layout={'lg': Layout(w=6, h=8, x=18, y=8, minW=6, minH=6)},
                ),
                WidgetHistogram(  # Energy density
                    title='Energy-density distribution',
                    x=f'data.energy_density#{SCHEMA}',
                    n_bins=100,
                    autorange=True,
                    unit='W*hour/kg',
                    layout={'lg': Layout(w=6, h=8, x=24, y=8, minW=6, minH=6)},
                ),
                # --- scatter plot (Voltage vs Capacity coloured by Specifier) --
                WidgetScatterPlot(
                    title='Voltage vs Capacity (by Specifier)',
                    x=Axis(
                        search_quantity=f'data.voltage#{SCHEMA}',
                        title='Voltage',
                    ),
                    y=Axis(
                        search_quantity=f'data.capacity#{SCHEMA}',
                        title='Capacity',
                        unit='mA*hour/g',
                    ),
                    # markers=Markers(
                    #     color=Axis(
                    #         search_quantity=f'data.specifier#{SCHEMA}',
                    #         title='Specifier',
                    #     )
                    # ),
                    size=800,
                    autorange=True,
                    layout={'lg': Layout(w=6, h=8, x=12, y=0, minW=6, minH=6)},
                ),
            ],
        ),
    ),
)

__all__ = ['battery_app']