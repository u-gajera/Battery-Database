# How to Use the NOMAD Battery Materials Plugin

This plugin provides a comprehensive toolkit for battery materials data. You can use it in two primary ways: to explore and visualize existing battery data through a dedicated application, or to contribute your own experimental or computational data to the database.

### 1. Exploring the Battery Database

The plugin features a powerful search and visualization interface designed specifically for battery materials data.

-   **Access the App**: To get started, navigate to the **Explore** menu in the NOMAD UI and select **Battery Database** under the **USE CASES** section.
-   **Search and Filter**: The application allows you to narrow down searches using a variety of filters, including:
    -   Material (by chemical formula)
    -   Journal and Publication Year
    -   Available quantitative properties (e.g., "Capacity" or "Voltage")
-   **Visualize Data**: An interactive dashboard automatically updates with your search results, offering several widgets for data visualization:
    -   A periodic table highlighting elements present in the results.
    -   Histograms showing the distribution of key properties like capacity, voltage, and energy density.
    -   A scatter plot of Voltage vs. Capacity to identify trends.
-   **Analyze Results**: A detailed and sortable table at the bottom displays all entries matching your search criteria, with columns for material, capacity, voltage, and more.
- [Additional Information can be found](search_data_in_app.md)

### 2. Adding Your Own Data

You can contribute your own battery data directly through the NOMAD interface by creating a new entry that conforms to the battery schema.

-   **Create a New Entry**:
    1.  Go to the **PUBLISH** menu and start a new upload.
    2.  In the upload section, click the **CREATE FROM SCHEMA** button.
    3.  Give your entry a name and select the **ChemDataExtractorBattery** schema from the built-in options.
-   **Add Data**:
    1.  Once the entry is created, navigate to the **DATA** tab.
    2.  Fill in the relevant quantitative properties for your material, such as `capacity`, `voltage`, `coulombic efficiency`, `energy density`, and the `material name`.
    3.  For better data integration, you can also define the material's chemical composition using the `PureSubstanceComponent` section.
-   **Publish**:
    1.  After entering all your data, return to the main upload page.
    2.  Review your entry and click **Publish** to make your data public. Your contribution will then be indexed and discoverable within the Battery Database application.

- [How to Upload Custom Battery Data](how_to_add_own_batterydata.md)