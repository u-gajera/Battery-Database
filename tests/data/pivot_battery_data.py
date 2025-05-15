import pandas as pd

def pivot_battery_data(input_file: str, output_file: str) -> None:
    """
    Reads a CSV file with battery property records and pivots the
    'Property' rows into separate columns for each compound (indexed by 'Name').
    Also preserves paper metadata (DOI, Title, Journal, Date, etc.) by taking
    the first occurrence for each compound.
    Saves the transformed DataFrame to a new CSV.
    """
    # Load the data
    df = pd.read_csv(input_file)
    
    # Drop any auto-index column if present
    if 'Unnamed: 0' in df.columns:
        df = df.drop(columns=['Unnamed: 0'])
    
    # Pivot the four measurement fields into wide form by 'Name'
    df_pivot = df.pivot_table(
        index='Name',
        columns='Property',
        values=['Value', 'Raw_value', 'Raw_unit', 'Unit'],
        aggfunc='first'
    )
    # Flatten the MultiIndex columns (e.g. ('Value','Capacity') -> 'Capacity_Value')
    df_pivot.columns = [f"{prop}_{measure}" for measure, prop in df_pivot.columns]
    df_pivot = df_pivot.reset_index()
    
    # Extract metadata columns and drop duplicates to get one row per compound
    meta_cols = [c for c in df.columns if c not in ['Property','Value','Raw_value','Raw_unit','Unit']]
    df_meta = df[meta_cols].drop_duplicates(subset='Name')
    
    # Merge metadata with pivoted measurements
    df_final = pd.merge(df_meta, df_pivot, on='Name', how='right')
    
    # Save the result
    df_final.to_csv(output_file, index=False)
    print(f"Pivoted data saved to: {output_file}")


if __name__ == "__main__":
    # Update file names/paths if necessary
    pivot_battery_data(
        input_file='test_battery_data.csv',
        output_file='test_battery_data_pivot.csv'
    )
