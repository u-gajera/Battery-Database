# Schema Reference

This page details the schema quantities defined in `nomad_battery_database.schema_packages.battery_schema.BatteryDatabase`. The data we are publishing here is extracted by Chemdataextractor and this work has been done by https://doi.org/10.1038/s41597-020-00602-2 . Feel free to let us know if you find any descripancy with original data here. 

### Core Information
-   `material_name` (str): The common name or label for the material entry.
-   `extracted_name` (str): A structured string representation of the chemical composition, e.g., `[{'Li': '1'}, {'Fe': '1'}]`.
-   `chemical_formula_hill` (str): The Hill-ordered chemical formula derived from `extracted_name`.
-   `elements` (list[str]): A list of elements present in the material.

### Bibliographic
-   `DOI` (str): The Digital Object Identifier of the source publication.
-   `title` (str): The title of the publication.
-   `journal` (str): The name of the journal.
-   `publication_year` (str): The year of publication, extracted from the publication date.
-   `publication` (PublicationReference): A sub-section containing structured bibliographic data.

### Quantitative Properties
For each property, there are typically three fields:
1.  A "raw value" field (e.g., `capacity_raw_value`) directly from the source file.
2.  A "raw unit" field (e.g., `capacity_raw_unit`).
3.  A standardized field with a default (more standard) unit (e.g., `capacity` with unit `mA*hour/g`).

-   **Capacity**
    -   `capacity_raw_value` (float)
    -   `capacity_raw_unit` (str)
    -   `capacity` (float, unit: `mA*hour/g`)
-   **Voltage**
    -   `voltage_raw_value` (float)
    -   `voltage_raw_unit` (str)
    -   `voltage` (float, unit: `V`)
-   **Coulombic Efficiency**
    -   `coulombic_efficiency_raw_value` (float)
    -   `coulombic_efficiency_raw_unit` (str)
    -   `coulombic_efficiency` (float)
-   **Energy Density**
    -   `energy_density_raw_value` (float)
    -   `energy_density_raw_unit` (str)
    -   `energy_density` (float, unit: `W*hour/kg`)
-   **Conductivity**
    -   `conductivity_raw_value` (float)
    -   `conductivity_raw_unit` (str)
    -   `conductivity` (float, unit: `S/cm`)

### Metadata and Filtering
-   `available_properties` (str): A human-readable summary of which quantitative properties are available for this entry (e.g., "Capacity and Voltage"). Used for filtering in the GUI.
-   `specifier` (str): A term describing the experimental conditions (e.g., "discharge capacity").
-   `tag` (str): A general-purpose tag for categorization.
-   `info` (str): Additional information about the measurement.