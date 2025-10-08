
# NOMAD Plugin for Battery Database

This repository contains the `nomad-battery-database` plugin, which allows you to parse, schematize, and visualize curated experimental battery properties from the literature within NOMAD. In addition to that, you can upload your own creation directly into the dataset. 

The plugin provides schemas for storing battery data and includes a parser to automatically process and upload datasets from tabular files. It is designed for two primary workflows: manually entering single data points and batch-uploading large datasets.

## Features

*   **Dual Schema System**: Includes a `Battery` schema for manual uploads and the more detailed `ChemDataExtractorBattery` schema for batch parsing.
*   **Flexible Parser**: The `BatteryParser` automatically processes `.csv`, `.xls`, and `.xlsx` files.
*   **Automated Normalization**: Automatically parses chemical compositions, generates Hill-ordered formulas, creates publication references from DOIs, and standardizes property values.
*   **Dedicated Search Application**: Provides a powerful, interactive user interface within NOMAD for exploring and visualizing the battery data.

## The Battery Database Application

Once your data is uploaded and processed, you can explore it using a dedicated application within NOMAD. This interface, defined in the plugin's `__init__.py` file, is designed for intuitive data discovery and visualization.

The application can be found by navigating to the **Explore** menu and selecting **Battery Database** under the "Use Cases" category.

The interface consists of three main components:

1.  **Filter Panel**: On the left, you can narrow your search by key metadata. Filters include `Material` (chemical formula), `Journal`, `Publication Year`, `Available Properties`, and more.
2.  **Interactive Dashboard**: A series of widgets at the top provide a visual summary of your search results. This includes a `Periodic Table` of a `Periodic Table` of the elements present, `Histograms` for the distribution of key properties (Capacity, Voltage, Energy Density), and `Scatter Plots` to visualize relationships between properties like Voltage vs. Capacity.
3.  **Results Table**: A detailed and sortable table at the bottom displays the entries matching your criteria. Default columns include `Material`, `Journal`, `Capacity`, `Voltage`, and `Energy Density`.

For a complete walkthrough of the application's features, see the [**Searching and Exploring Battery Data**](docs/how_to/search_data_in_app.md) guide.

## Getting Started

To get started with adding your own data, follow our step-by-step guides.

*   For a complete walkthrough from a raw CSV file to the final visualization, see our [**Tutorial**](docs/tutorial/tutorial.md).
*   To upload data in batches using the parser, refer to the guide on [**How to Prepare and Upload Data**](docs/how_to/use_this_plugin.md).
*   To manually add a single data point through the NOMAD interface, see [**How to Add Your Own Battery Data**](docs/how_to/how_to_add_own_batterydata.md).

## Documentation

This README provides a high-level overview. For detailed information on the schemas, parser, and contribution guidelines, please refer to our full documentation.

*   [**View the full documentation**](docs/index.md)

## Installation

To add this plugin to your NOMAD or NOMAD Oasis instance, please follow the official [**NOMAD plugin installation instructions**](https://nomad-lab.eu/prod/v1/docs/howto/plugins/plugins.html).

## Contributing

Contributions are very welcome! If you would like to help improve the plugin or its documentation, please read our [**contribution guide**](docs/how_to/contribute_to_this_plugin.md).

## Development and Installation
If you want to develop this plugin locally, clone the project and create a virtual environment (you can use Python 3.9, 3.10, or 3.11):

```
git clone https://github.com/u-gajera/Battery-Database.git
cd Battery-Database
python3.11 -m venv .pyenv
source .pyenv/bin/activate
```
Make sure to have pip upgraded:
```
pip install --upgrade pip
```
We recommend installing uv for fast package installation:
```
pip install uv
```
Install the plugin in editable mode with its development dependencies:

```
uv pip install -e '....
```
### Run the Tests
You can run the tests locally:
```
pytest -sv tests
```

To generate a local coverage report:

```
uv pip install pytest-cov
pytest --cov=src tests
```

### Auto-formatting
We use Ruff for linting and formatting the code.

```
ruff check .
ruff format .
```

Main Contributors
Dr. Uday Gajera,	uday.gajera@physik.hu-berlin.de

Current data source
Data Source: https://doi.org/10.1038/s41597-020-00602-2
