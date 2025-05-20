from __future__ import annotations
from pathlib import Path
from typing import Iterator

import pandas as pd
import yaml
from nomad.datamodel import EntryArchive
from nomad.parsing import MatchingParser

from ..schema_packages.battery import BatteryDatabase, BatteryProperties


class BatteryParser(MatchingParser):
    """Parse CSV or YAML files from the curated battery database."""

    def __init__(self, **kwargs):  # kwargs populated by EntryPoint (e.g. regex)
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
            logger and logger.debug("added CSV row", row_index=idx, material=props.material_name)

    @staticmethod
    def _parse_yaml(path: Path, archive: EntryArchive, logger=None) -> None:
        with path.open("r", encoding="utf-8") as fh:
            mapping = yaml.safe_load(fh) or {}
        db = archive.data = BatteryDatabase()
        props = BatteryProperties()
        BatteryParser._update_from_mapping(props, mapping)
        db.Material_entries.append(props)
        logger and logger.info("parsed YAML", file=path.name, material=props.material_name)

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
                else:
                    setattr(props, attr, value)


_ALIASES = {                       # ← 1️⃣  add canonical names here
    "name": "material_name",
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