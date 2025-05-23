from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import pandas as pd
import yaml
from nomad.datamodel import EntryArchive
from nomad.parsing import MatchingParser

from nomad_battery_database.schema_packages.battery_schema import (
    BatteryDatabase,
    BatteryProperties,
)

# ----------------------------------------------------------
# Chemistry util – build Hill formula from the 'Extracted_name' column
# ----------------------------------------------------------
COUNT_TOLERANCE: float = 1e-2

def _safe_literal_eval(raw: str) -> list[dict[str, Any]] | None:
    try:
        evaluated = ast.literal_eval(raw)
        if isinstance(evaluated, list):
            return evaluated
    except (ValueError, SyntaxError, TypeError):
        pass
    return None

def _normalize_parts(raw: str | list | None) -> list[dict[str, Any]] | None:
    if raw is None:
        return None
    if isinstance(raw, str):
        return _safe_literal_eval(raw)
    if isinstance(raw, list):
        return raw
    return None

def _merge_element_counts(parts: list[dict[str, Any]]) -> dict[str, float] | None:
    totals: dict[str, float] = {}
    for part in parts:
        if not isinstance(part, dict):
            continue
        for elem, cnt in part.items():
            try:
                n = float(str(cnt))
            except (ValueError, TypeError):
                return None
            totals[elem] = totals.get(elem, 0.0) + n
    return totals

def _format_formula(totals: dict[str, float]) -> str | None:
    elems = []
    if "C" in totals:
        elems.append("C")
        if "H" in totals:
            elems.append("H")
    elems += [e for e in sorted(totals) if e not in {"C", "H"}]

    formula = ""
    for el in elems:
        n = totals[el]
        if abs(n - 1.0) < COUNT_TOLERANCE:
            formula += el
        else:
            formula += f"{el}{int(n) if n.is_integer() else n}"
    return formula or None

def _hill_from_extracted(raw: str | list | None) -> str | None:
    """
    Convert the string representation of ``Extracted_name`` to a Hill-ordered formula.
    """
    parts = _normalize_parts(raw)
    if not parts:
        return None
    totals = _merge_element_counts(parts)
    if totals is None:
        return None

    return _format_formula(totals)


# ----------------------------------------------------------
class BatteryParser(MatchingParser):
    """Parse CSV or YAML files from the curated battery database."""

    def __init__(self, **kwargs):  
        super().__init__(**kwargs)

    # ----------------------------------------------------------
    # Mandatory parse       (MatchingParser already checks regex)
    # ----------------------------------------------------------
    def parse(
        self,
        mainfile: str,
        archive: EntryArchive,
        logger=None,
        child_archives: dict[str, EntryArchive] | None = None,
    ) -> None:  # noqa: D401, N802 – NOMAD API
        path = Path(mainfile)
        if path.suffix.lower() == ".csv":
            self._parse_csv(path, archive, logger)
        else:
            self._parse_yaml(path, archive, logger)

    # ----------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------
    @staticmethod
    def _parse_csv(path: Path, archive: EntryArchive, logger=None) -> None:
        df = pd.read_csv(path)
        db = archive.data = BatteryDatabase()
        for idx, row in df.iterrows():
            props = BatteryParser._row_to_props(row)
            db.Material_entries.append(props)
            logger and logger.debug("added CSV row", 
                                    row_index=idx, 
                                    material=props.material_name)

    @staticmethod
    def _parse_yaml(path: Path, archive: EntryArchive, logger=None) -> None:
        with path.open("r", encoding="utf-8") as fh:
            mapping = yaml.safe_load(fh) or {}
        db = archive.data = BatteryDatabase() 

        # Assuming a single YAML file corresponds to one material entry for now
        # If a YAML can contain multiple entries, this part needs adjustment
        if isinstance(mapping, list) and all(isinstance(item, 
                                                        dict) for item in mapping):
            # This handles if the YAML root is a list of material entries
            for idx, entry_map in enumerate(mapping):
                props = BatteryProperties()
                BatteryParser._update_from_mapping(props, entry_map)
                db.Material_entries.append(props)
                logger and logger.info("parsed YAML entry", 
                                       file=path.name, 
                                       entry_index=idx, 
                                       material=props.material_name)
        elif isinstance(mapping, dict):
            # This handles if the YAML root is a single material entry
            props = BatteryProperties()
            BatteryParser._update_from_mapping(props, mapping)
            db.Material_entries.append(props)
            logger and logger.info("parsed YAML", 
                                   file=path.name, 
                                   material=props.material_name)
        else:
            logger and logger.error("Unsupported YAML structure", 
                                    file=path.name, type=type(mapping))


    # ---------- util ----------
    @staticmethod
    def _safe_float(value: object) -> float | None:
        """Return *first* float found in a messy numeric cell.

        Handles strings like "8.25 , 11.13 and 18.46", parentheses, inequality
        signs, etc.  The strategy is to scan left‑to‑right and return the first
        token that can be interpreted as a *float*.
        """
        import re

        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None

        if isinstance(value, (int, float)):
            return float(value)

        # Treat as str – normalise delimiters
        text = str(value)
        text = text.replace(";", ",").replace(" and ", ",")
        # Split on everything that is *not* part of a float literal
        tokens = re.split(r"[^0-9eE+\-.]+", text)
        for tok in tokens:
            if tok in {"", "+", "-", "."}:
                continue
            try:
                return float(tok)
            except ValueError:
                continue
        return None

    @staticmethod
    def _row_to_props(row: pd.Series) -> BatteryProperties:
        props = BatteryProperties()
        # strings --------------------------------------------------------
        for col in [
            "Name", "Extracted_name", "title", "DOI", "journal", "date",
            "specifier", "tag", "warning", "correctness", "material_type", "info",
        ]:
            if col in row and pd.notna(row[col]):
                setattr(props, _col_to_attr(col), str(row[col]).strip())

        # ---------- derived chemistry ----------
        # This is called before Metainfo stringifies extracted_name if it was a list
        if props.extracted_name and not props.chemical_formula_hill:
            hill = _hill_from_extracted(props.extracted_name) 
            if hill:
                props.chemical_formula_hill = hill
        # numbers --------------------------------------------------------
        for label, attr in [
            ("Capacity", "capacity"),
            ("Voltage", "voltage"),
            ("Coulombic_efficiency", "coulombic_efficiency"),
            ("Energy_density", "energy_density"),
            ("Conductivity", "conductivity"),
        ]:
            raw_val = row.get(f"{label}_Raw_value")
            raw_unit = row.get(f"{label}_Raw_unit")
            num = BatteryParser._safe_float(raw_val)
            if num is not None:
                setattr(props, f"{attr}_raw_value", num)
            if pd.notna(raw_unit):
                setattr(props, f"{attr}_raw_unit", str(raw_unit))
        return props

    @staticmethod
    def _update_from_mapping(props: BatteryProperties, mapping: dict) -> None:
        for key, value in mapping.items():
            attr = _col_to_attr(key)
            if hasattr(props, attr):
                if attr.endswith("_raw_value") and isinstance(value, str):
                    num = BatteryParser._safe_float(value)
                    if num is not None:
                        setattr(props, attr, num)
                    # else: value is kept as string if _safe_float returns None,
                    # Metainfo will try to coerce or raise error if type is float64
                else:
                    setattr(props, attr, value) # value can be list for extracted_name

        # compute Hill formula once all attributes are set
        # This is called before Metainfo stringifies extracted_name if it was a list
        if props.extracted_name and not props.chemical_formula_hill:
            # props.extracted_name will be what was in 'value' from (str or list)
            hill = _hill_from_extracted(props.extracted_name)
            if hill:
                props.chemical_formula_hill = hill


_ALIASES = {
    "name": "material_name",
    "doi": "DOI",
    # put other future synonyms here if needed
}

def _col_to_attr(column: str) -> str:
    """
    Map CSV/YAML column names → :class:`BatteryProperties` attributes.
    Keeps the previous *lower-case/underscore* rule but honours explicit
    aliases first.
    """
    key = column.strip().lower().replace(" ", "_")
    return _ALIASES.get(key, key)

# Note on _parse_yaml: The provided example YAML seems to represent a single material.
# If a YAML file could contain a list of materials at its root, _parse_yaml might need
# to iterate through that list and create multiple BatteryProperties instances.
