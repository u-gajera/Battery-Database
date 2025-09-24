"""
CSV → YAML *without* any NOMAD dependency
========================================

A minimal script that converts **each row** of a CSV file into a structured YAML file.

Usage
-----
$ python split_csv_to_yaml.py --csv battery_data_pivot.extracted_battery.csv  \
        --schema ../../src/nomad_battery_database/schema_packages/battery_schema.py  \
        --outdir yaml_rows

*   Every row becomes a structured YAML file `entries/entry1.extracted_battery.yaml`.
*   Missing columns are reported once at the end.

Dependenciesc
------------
- pandas
- pyyaml

Install with e.g.  `pip install pandas pyyaml`
"""

from __future__ import annotations

import argparse
import ast
import re
from pathlib import Path

import pandas as pd
import yaml

KEY_MAP = {
    'Name': 'material_name',
    'Extracted_name': 'extracted_name',
    'DOI': 'doi',
    'Specifier': 'specifier',
    'Tag': 'tag',
    'Title': 'title',
    'Journal': 'journal',
    'Date': 'date',
    'Correctness': 'correctness',
    'Capacity_Raw_unit': 'capacity_raw_unit',
    'Capacity_Raw_value': 'capacity_raw_value',
    'Capacity_Unit': 'capacity_unit',
    'Capacity_Value': 'capacity',
}

def _collect_schema_names(schema_path: Path) -> set[str]:
    """Return *all* Quantity names found in the given schema file.

    We scan the file textually so that **no import is necessary**
    (avoids the need for the NOMAD SDK or any third‑party code).
    """
    pattern_q = re.compile(r"Quantity\s*\(\s*['\"](?P<name>[A-Za-z0-9_]+)['\"]")
    names: set[str] = set()
    with schema_path.open("r", encoding="utf‑8") as fh:
        for line in fh:
            m = pattern_q.search(line)
            if m:
                names.add(m.group("name"))
    return names

def _parse_extracted_name(value: str) -> list[dict] | None:
    """Safely parse the string representation of a list of dictionaries."""
    if not isinstance(value, str):
        return None
    try:
        parsed_list = ast.literal_eval(value)
        if not isinstance(parsed_list, list):
            return None

        cleaned_list = []
        for item in parsed_list:
            if isinstance(item, dict):
                cleaned_item = {
                    k: float(v) if isinstance(v, str) and v.replace('.',
                                                        '', 1).isdigit() else v
                    for k, v in item.items()
                }
                cleaned_list.append(cleaned_item)
        return cleaned_list
    except (ValueError, SyntaxError):
        print(f"[WARN] Could not parse Extracted_name: {value}")
        return None

def transform_row_to_dict(row: pd.Series) -> dict:
    """
    Transforms a pandas Series (a row) into the target nested dictionary structure.
    """
    data = {
        "m_def": "nomad_battery_database.schema_packages.battery_schema.ChemDataExtractorBattery"
    }

    for col, value in row.dropna().items():

        if col == 'Extracted_name':
            parsed_value = _parse_extracted_name(value)
            if parsed_value:
                data['extracted_name'] = parsed_value

        elif col == 'Info':
            if isinstance(value, str):
                try:
                    parsed_dict = ast.literal_eval(value)
                    if isinstance(parsed_dict, dict):
                        cleaned_dict = {}
                        for k, v in parsed_dict.items():
                            if isinstance(v, str):
                                try:
                                    cleaned_dict[k] = ast.literal_eval(v)
                                except (ValueError, SyntaxError):
                                    cleaned_dict[k] = v
                            else:
                                cleaned_dict[k] = v
                        data['info'] = cleaned_dict
                except (ValueError, SyntaxError):
                    print(f"[WARN] Could not parse 'Info' as a dictionary: {value}")

        else:
            key = KEY_MAP.get(col, col.lower()) 
            native_value = value.item() if hasattr(value, "item") else value
            data[key] = native_value

    return {"data": data}

def csv_to_yaml(
    csv_path: Path,
    schema_path: Path | None = None,
    outdir: Path = Path("entries"),
    index_base: int = 1,
) -> None:
    df = pd.read_csv(csv_path, dtype=str)
    for col in df.columns:
        try:
            df[col] = pd.to_numeric(df[col])
        except (ValueError, TypeError):
            pass

    print(f"[INFO] CSV loaded: {len(df)} rows, {len(df.columns)} columns.")

    schema_names: set[str] = set()
    if schema_path is not None and schema_path.exists():
        schema_names = _collect_schema_names(schema_path)
        print(f"[INFO] Schema parsed: {len(schema_names)} quantity names collected.")

        handled_cols = set(KEY_MAP.keys()) | {'Info'} 
        unmapped_df_cols = set(df.columns) - handled_cols
        schema_mapped_cols = {col.lower() for col in unmapped_df_cols} 

        unknown_cols = sorted(schema_mapped_cols - schema_names)
        if unknown_cols:
            print("[WARN] The following CSV columns are NOT in the schema:")
            for c in sorted(unmapped_df_cols):
                 print(f"       • {c}")

    elif schema_path is not None:
        print(f"[WARN] Schema '{schema_path}' does not exist – skipping validation.")
    outdir.mkdir(parents=True, exist_ok=True)

    for idx, row in df.iterrows():
        row_number = idx + index_base
        out_file = outdir / f"entry{row_number}.archive.yaml"

        mapping = transform_row_to_dict(row)

        with out_file.open("w", encoding="utf‑8") as fh:
            yaml.safe_dump(
                mapping,
                fh,
                allow_unicode=True,
                sort_keys=False,
                default_flow_style=False,
                width=160,
            )
        print(f"[OK] Wrote {out_file} (keys: {len(mapping['data'])})")

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="CSV → one‑YAML‑per‑row converter")
    parser.add_argument("--csv", type=Path, required=True, help="Input CSV file")
    parser.add_argument("--schema", type=Path, default=None,
                        help="Schema .py file for name checks")
    parser.add_argument("--outdir", type=Path, default=Path("entries"),
                        help="Output directory")
    args = parser.parse_args(argv)

    csv_to_yaml(args.csv, args.schema, args.outdir)


if __name__ == "__main__":
    main()