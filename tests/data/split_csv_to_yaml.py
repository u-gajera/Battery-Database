"""
CSV → YAML *without* any NOMAD dependency
========================================

A minimal script that converts **each row** of `test_battery_data_pivot.csv` 

Usage
-----
$ python csv_to_yaml.py --csv test_battery_data_pivot.csv  \
                       --schema battery.py               \
                       --outdir entries

*   Every row becomes `entries/battery_00001.yaml`, `entries/battery_00002.yaml`, …
*   Missing columns are reported once at the end, so you can keep your nome tidy.

Dependencies
------------
- pandas
- pyyaml

Install with e.g.  `pip install pandas pyyaml`
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd
import yaml

###############################################################################
# Helpers
###############################################################################

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

###############################################################################
# Core conversion logic
###############################################################################

def csv_to_yaml(
    csv_path: Path,
    schema_path: Path | None = None,
    outdir: Path = Path("entries"),
    index_base: int = 1,
) -> None:
    # ------------------------------------------------------------------
    # 1. Read CSV
    # ------------------------------------------------------------------
    df = pd.read_csv(csv_path)
    print(f"[INFO] CSV loaded: {len(df)} rows, {len(df.columns)} columns.")

    # ------------------------------------------------------------------
    # 2. Optionally parse schema to validate column names
    # ------------------------------------------------------------------
    schema_names: set[str] = set()
    if schema_path is not None and schema_path.exists():
        schema_names = _collect_schema_names(schema_path)
        print(f"[INFO] Schema parsed: {len(schema_names)} quantity names collected.")

        unknown_cols = sorted(set(df.columns) - schema_names)
        if unknown_cols:
            print("[WARN] The following CSV columns are NOT in the schema:")
            for c in unknown_cols:
                print(f"       • {c}")
    elif schema_path is not None:
        print(f"[WARN] Schema '{schema_path}' does not exist – skipping validation.")

    # ------------------------------------------------------------------
    # 3. Ensure output directory exists
    # ------------------------------------------------------------------
    outdir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 4. Write one YAML per row
    # ------------------------------------------------------------------
    for idx, row in df.iterrows():
        row_number = idx + index_base
        out_file = outdir / f"battery_{row_number:05d}.yaml"

        # Drop NaNs so the YAML stays clean and lightweight
        mapping = (
            row.dropna()
            .apply(lambda v: v.item() if hasattr(v, "item") else v)  # unwrap NumPy
            .to_dict()
        )

        with out_file.open("w", encoding="utf‑8") as fh:
            yaml.safe_dump(
                mapping,
                fh,
                allow_unicode=True,
                sort_keys=False,
                default_flow_style=False,
                width=160,
            )
        print(f"[OK] Wrote {out_file} (keys: {len(mapping)})")

###############################################################################
# CLI wrapper
###############################################################################

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
