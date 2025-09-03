# Battery-Database Plugin for NOMAD

This NOMAD plugin provides a comprehensive tool for parsing, storing, and exploring curated experimental battery data from scientific literature. It defines a dedicated schema for battery properties and creates an interactive application within NOMAD for analyzing the collected data.

## Key Features

*   **Custom Parser:** Ingests battery data from common file formats, including CSV, Excel (`.xls`, `.xlsx`), and YAML.
*   **Dedicated Data Schema:** Defines a `BatteryDatabase` schema that captures key performance metrics like capacity, voltage, coulombic efficiency, energy density, and conductivity, alongside rich bibliographic metadata.
*   **Interactive Application:** Provides a dedicated search page at `/batterydb` with powerful filtering capabilities, a periodic table of elements, histograms for property distributions, and scatter plots for exploring relationships between key metrics.

## Data Formats

To use this plugin, your data must be structured in one of the following formats.

### YAML Format

The parser accepts YAML files containing a list of entries, where each entry is a dictionary of key-value pairs. This format is ideal for structured, human-readable data.

**Example (`entry1.extracted_battery.yaml`):**
```yaml
- Name: LiCoO2
  DOI:
    - "10.1016/j.electacta.2016.11.154"
  Capacity_Raw_value: 140
  Capacity_Raw_unit: mAh/g
  Voltage_Raw_value: 3.7
  Voltage_Raw_unit: V

- Name: Na3V2(PO4)3
  DOI: ["10.1039/C4NR06432A"]
  Capacity_Raw_value: 105
  Capacity_Raw_unit: mAh/g
  Voltage_Raw_value: 3.4
  Voltage_Raw_unit: V 
  ```

### CSV/Excel Format
The parser can also process tabular data from CSV or Excel files. The file should contain one row per entry, with columns corresponding to the schema fields.

Example (battery_data_pivot.extracted_battery.csv):

```
code
csv
Name,DOI,Capacity_Raw_value,Capacity_Raw_unit,Voltage_Raw_value,Voltage_Raw_unit
LiCoO2,"10.1016/j.electacta.2016.11.154; 10.1038/s41597-020-00602-2",140,mAh/g,3.7,V
"Na3V2(PO4)3","10.1039/C4NR06432A",105,mAh/g,3.4,V
```

## Development and Installation
If you want to develop this plugin locally, clone the project and create a virtual environment (you can use Python 3.9, 3.10, or 3.11):

```code
Sh
git clone https://github.com/u-gajera/Battery-Database.git
cd Battery-Database
python3.11 -m venv .pyenv
source .pyenv/bin/activate
```
Make sure to have pip upgraded:
```code
Sh
pip install --upgrade pip
```
We recommend installing uv for fast package installation:
```code
Sh
pip install uv
```
Install the plugin in editable mode with its development dependencies:

```code
Sh
uv pip install -e '....
```
### Run the Tests
You can run the tests locally:
```code
Sh
pytest -sv tests
```

To generate a local coverage report:

```code
Sh
uv pip install pytest-cov
pytest --cov=src tests
```

### Auto-formatting
We use Ruff for linting and formatting the code.

```code
Sh
ruff check .
ruff format .
```

Main Contributors
Name	E-mail
Uday Gajera	uday.gajera@physik.hu-berlin.de
