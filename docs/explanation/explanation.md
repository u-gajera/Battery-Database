# Explanation

This section provides background on the plugin's design and functionality.

### Parser Logic

The `BatteryParser` is the core component responsible for reading your data files and populating the schema.

-   **File Matching (`does_match`)**: The parser first checks if a file is likely to contain battery data.
    -   For `.yaml`/`.yml` files, it looks for the presence of characteristic keys like `Extracted_name:` and `DOI:`.
    -   For `.csv` files, it checks the header row for columns like `Name,` and `Capacity_Raw_value,`.
    This ensures that the parser only attempts to process relevant files.
-   **Data Ingestion**:
    -   **Tables (CSV/XLSX)**: The parser reads the table row by row. Each row is treated as a separate NOMAD entry. It maps column headers (e.g., `Capacity_Raw_value`) to the schema attributes (e.g., `capacity_raw_value`) using the `_col_to_attr` function, which handles case-insensitivity and aliases.
    -   **YAML**: It loads the YAML file. If the file is a dictionary, it creates a single entry. If it's a list of dictionaries, it creates one entry for each item in the list.
-   **Value Cleaning (`_safe_float`)**: Raw data files often contain non-numeric characters or multiple values in a single cell (e.g., "217 mAhg-1"). This function robustly extracts the first valid floating-point number from a string.

### Schema and Normalization

The `BatteryDatabase` class in `battery_schema.py` defines the structure of the data. The `normalize` method is a special function that NOMAD calls after a parser has finished. It is used to clean, augment, and standardize the data.

-   **Chemical Formula Derivation**: The raw `Extracted_name` (e.g., `[{'Cu': '1.0', 'O': '1.0'}]`) is parsed to generate a standard Hill-ordered chemical formula (`CuO`). This standardized formula is crucial for searching and filtering. It also populates the `elements` and `elemental_composition` fields in the NOMAD `results` section, which powers the periodic table widget.
-   **Unit Handling**: The schema defines standard units for key quantities (e.g., `capacity` in `mA*hour/g`). The normalizer copies the raw values (like `capacity_raw_value`) to the standardized fields (`capacity`) and attempts to parse the raw unit string.
-   **Publication Linking**: If a `DOI` is provided, the normalizer automatically creates a `PublicationReference` section, which allows NOMAD to fetch bibliographic details and link to the original paper (Base feature in Nomad).
-   **available_properties**: To make filtering easier, the normalizer checks which quantitative properties (Capacity, Voltage, etc.) are present in the entry and generates a human-readable string (e.g., "Capacity and Voltage"). This string is then used to create a filter in the GUI. (we are trying to create better filters for according to your need, feel free to provide feed back if any important features are missing.)