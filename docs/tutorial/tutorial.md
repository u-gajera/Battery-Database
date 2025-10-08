# Tutorial: From Raw Data to Interactive Visualization

This tutorial will guide you through the complete workflow of preparing experimental battery data, converting it into a NOMAD-compatible format, uploading it, and exploring it using the interactive GUI.

We will use the utility scripts provided in the project to process the data.

### 1. Initial Data Format

Let's assume your raw data is in a "long" CSV format, where each row represents a single property for a given material. This format is common for aggregating data from different sources (Format provided in the https://doi.org/10.1038/s41597-020-00602-2 paper).

Create a file named `raw_battery_data.csv` with the following content:

```csv
Name,Extracted_name,DOI,Specifier,Property,Value,Raw_value,Raw_unit,Unit
40-CuO / C,"[{'Cu': '1.0', 'O': '1.0'}, {'C': '1.0'}]",10.1039/C4NR06432A,discharge capacity,Capacity,217.0,217,mAhg−1,"Gram^(-1.0) Hour(1.0) MilliAmpere(1.0)"
40-CuO / C,"[{'Cu': '1.0', 'O': '1.0'}, {'C': '1.0'}]",10.1039/C4NR06432A,discharge voltage,Voltage,1.5,1.5,V,Volt(1.0)
LixMn2O4,"[{'Li': 'x', 'Mn': '2.0', 'O': '4.0'}]",10.1016/j.jpowsour.2014.07.191,charge capacity,Capacity,120.0,120,mAh/g,"Gram^(-1.0) Hour(1.0) MilliAmpere(1.0)"
LixMn2O4,"[{'Li': 'x', 'Mn': '2.0', 'O': '4.0'}]",10.1016/j.jpowsour.2014.07.191,charge voltage,Voltage,4.1,4.1,V,Volt(1.0)
LixMn2O4,"[{'Li': 'x', 'Mn': '2.0', 'O': '4.0'}]",10.1016/j.jpowsour.2014.07.191,efficiency,Coulombic_efficiency,98.5,98.5,%,Percent(1.0)
```

### 2. Pivoting the Data
The NOMAD parser expects the data in a "wide" format, where each row contains all properties for a single material. We use the pivot_battery_data.py script to perform this transformation.

#### Run the script:

```
python pivot_battery_data.py --input_file raw_battery_data.csv --output_file pivoted.extracted_battery.csv
This will create a new file, pivoted.extracted_battery.csv, with the following structure:
```

```
Name,Extracted_name,DOI,Capacity_Value,Voltage_Value,Coulombic_efficiency_Value,...
"40-CuO / C","[{'Cu': '1.0', 'O': '1.0'}, {'C': '1.0'}]",10.1039/C4NR06432A,217.0,1.5,,...
LixMn2O4,"[{'Li': 'x', 'Mn': '2.0', 'O': '4.0'}]",10.1016/j.jpowsour.2014.07.191,120.0,4.1,98.5,...
```

##### Note: The new pivoted script also pivots Raw_value, Raw_unit, and Unit columns.

### 3. Splitting CSV into Individual YAML Entries
If you feel comfortable with individual file, each material entry can be in its own file. This allows for independent processing and referencing. The parser is optimized for YAML files. We'll use the split_csv_to_yaml.py script.

#### Run the script:

```
python split_csv_to_yaml.py --csv pivoted.extracted_battery.csv --outdir entries
This command will create an entries directory and populate it with YAML files, one for each row in the pivoted CSV.
```
For example, entries/entry1.extracted_battery.yaml will contain:

```
Name: 40-CuO / C
Extracted_name: '[{''Cu'': ''1.0'', ''O'': ''1.0''}, {''C'': ''1.0''}]'
DOI: 10.1039/C4NR06432A
Specifier: discharge capacity
Capacity_Value: 217.0
Capacity_Raw_value: 217.0
Capacity_Raw_unit: mAhg−1
Capacity_Unit: Gram^(-1.0) Hour(1.0) MilliAmpere(1.0)
Voltage_Value: 1.5
Voltage_Raw_value: 1.5
Voltage_Raw_unit: V
Voltage_Unit: Volt(1.0)
```

### 4. Uploading to NOMAD
Now that the data is prepared, you can upload it to your NOMAD instance.

1. Navigate to the **UPLOAD** page in NOMAD.  
2. Click the **"New Upload"** button.  
3. You can either drag-and-drop the `entries` directory (zipped) or select it using the file browser.  
4. Add a name for your upload (e.g., *"My Battery Data"*) and click **UPLOAD**.  

NOMAD will automatically detect the csv/YAML files, match them to the battery parser, process them, and create the corresponding entries.
 ##### Note: It is important to have following extension in order to detect by Nomad: *.extracted_battery.csv or *..extracted_battery.yaml

---

### 5. Exploring the Data in the Battery App
Once the processing is complete (the upload status will change from "processing" to "finished"), you can explore the data.

1. Navigate to the **EXPLORE** page.  
2. From the **"Category"** dropdown, click on the **Battery Database** application.  

You will see a dashboard with:

- An interactive periodic table showing the elements present in your data.  
- Histograms for the distribution of Capacity, Voltage, and other quantitative properties.  
- A scatter plot of Voltage vs. Capacity.  
- A results table showing key data for each entry.  

On the left-hand side as well as below, you can use the filters to narrow down your search, for example, by **Journal**, **Publication Year**, or **Available Properties**. This allows you to quickly find and compare the materials you are interested in.
