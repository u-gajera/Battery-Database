from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any, Optional, Union

import numpy as np
import pandas as pd
from nomad.datamodel import EntryArchive
from nomad.parsing import MatchingParser

from nomad_battery_database.parsers.utils import create_archive
from nomad_battery_database.schema_packages.battery_schema import BatteryDatabase

COUNT_TOLERANCE: float = 1e-2


def _safe_literal_eval(raw: str) -> Optional[list[dict[str, Any]]]:
    try:
        evaluated = ast.literal_eval(raw)
        if isinstance(evaluated, list):
            return evaluated
    except (ValueError, SyntaxError, TypeError):
        pass
    return None


def _normalize_parts(raw: Optional[Union[str, list]]) -> Optional[list[dict[str, Any]]]:
    if raw is None:
        return None
    if isinstance(raw, str):
        return _safe_literal_eval(raw)
    if isinstance(raw, list):
        return raw
    return None


def _merge_element_counts(parts: list[dict[str, Any]]) -> Optional[dict[str, float]]:
    totals: dict[str, float] = {}
    for part in parts:
        for elem, cnt in part.items():
            try:
                n = float(str(cnt))
            except Exception:
                # simply skip unparseable counts such as 'x-3'
                continue
            totals[elem] = totals.get(elem, 0.0) + n
    return totals or None


def _format_formula(totals: dict[str, float]) -> Optional[str]:
    elems = []
    if 'C' in totals:
        elems.append('C')
        if 'H' in totals:
            elems.append('H')
    elems += [e for e in sorted(totals) if e not in {'C', 'H'}]

    formula = ''
    for el in elems:
        n = totals[el]
        if abs(n - 1.0) < COUNT_TOLERANCE:
            formula += el
        else:
            formula += f'{el}{int(n) if n.is_integer() else n}'
    return formula or None


def _hill_from_extracted(raw: Optional[Union[str, list]]) -> Optional[str]:
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


class BatteryParser(MatchingParser):
    """Parse CSV or YAML files from the curated battery database."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def parse(
        self,
        mainfile: str,
        archive: EntryArchive,
        logger=None,
        child_archives: Optional[dict[str, EntryArchive]] = None,
    ) -> None:
        path = Path(mainfile)
        self._parse_table(path, archive, logger)

    @staticmethod
    def _parse_table(path: Path, archive: EntryArchive, logger=None) -> None:
        ext = path.suffix.lower()
        if ext in {'.xls', '.xlsx'}:
            df = pd.read_excel(path).replace(np.nan, None)
        else:  # falls back to CSV
            df = pd.read_csv(path).replace(np.nan, None)

        # iterate rows → one BatteryDatabase per row
        for idx, row in df.iterrows():
            db = BatteryDatabase()
            BatteryParser._populate_entry_from_row(db, row)
            
            # Create a child archive file
            entry_name = (
                (db.material_name or f'row_{idx}').replace(' ', '_').replace('/', '_')
            )
            file_name = f'{entry_name}.battery.archive.json'

            create_archive(db, archive, file_name)
            logger and logger.info('archive_created', file=file_name, row_index=idx)

    @staticmethod
    def _safe_float(value: object) -> Optional[float]:
        """Return *first* float found in a messy numeric cell."""

        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None

        if isinstance(value, (int, float)):
            return float(value)

        text = str(value)
        text = text.replace(';', ',').replace(' and ', ',')
        tokens = re.split(r'[^0-9eE+\-.]+', text)
        for tok in tokens:
            if tok in {'', '+', '-', '.'}:
                continue
            try:
                return float(tok)
            except ValueError:
                continue
        return None

    @staticmethod
    def _populate_entry_from_row(db: BatteryDatabase, row: pd.Series) -> None:
        for col, value in row.items():
            if pd.isna(value):
                continue

            attr = _col_to_attr(col)
            if not hasattr(db, attr):
                continue

            if attr in {'extracted_name', 'info'}:
                if isinstance(value, str):
                    try:
                        parsed_value = ast.literal_eval(value)
                        setattr(db, attr, parsed_value)
                    except (ValueError, SyntaxError):
                        pass
                continue

            if attr.endswith(('_value', '_raw_value')):
                num = BatteryParser._safe_float(value)
                if num is not None:
                    setattr(db, attr, num)
                continue

            if attr.endswith(('_unit', '_raw_unit')):
                setattr(db, attr, str(value).strip())
                continue

            setattr(db, attr, str(value).strip())

        # ---------- derived chemistry ----------
        if db.extracted_name and not db.chemical_formula_hill:
            hill = _hill_from_extracted(db.extracted_name)
            if hill:
                db.chemical_formula_hill = hill
        # numbers --------------------------------------------------------
        for label, attr in [
            ('Capacity', 'capacity'),
            ('Voltage', 'voltage'),
            ('Coulombic_efficiency', 'coulombic_efficiency'),
            ('Energy_density', 'energy_density'),
            ('Conductivity', 'conductivity'),
        ]:
            val = row.get(f'{label}_Value')
            num = BatteryParser._safe_float(val)
            if num is not None:
                setattr(db, attr, num)

            raw_val = row.get(f'{label}_Raw_value')
            raw_unit = row.get(f'{label}_Raw_unit')
            num = BatteryParser._safe_float(raw_val)
            if num is not None:
                setattr(db, f'{attr}_raw_value', num)
            if pd.notna(raw_unit):
                setattr(db, f'{attr}_raw_unit', str(raw_unit))

    def does_match(self, mainfile: str, mainfile_content: bytes, logger):
        logger.info(f'BatteryParser.does_match attempting to confirm match for {mainfile}')
        if mainfile.endswith('.csv'):
            try:
                content_str = mainfile_content.decode('utf-8', errors='ignore')
                first_line = content_str.splitlines()[0]
                if 'Name,' in first_line and 'Capacity_Raw_value,' in first_line:
                    logger.info('BatteryParser.does_match confirmed for CSV.')
                    return True
                else:
                    logger.info(
                        'BatteryParser.does_match rejected for CSV: Missing characteristic headers.'
                    )
                    return False
            except Exception as e:
                logger.warning(f'BatteryParser.does_match encountered an error: {e}')
                return False

        if mainfile.endswith(('.xls', '.xlsx')):
            logger.info('BatteryParser.does_match confirmed for Excel by extension.')
            return True

        return False


_ALIASES = {
    'name': 'material_name',
    #'doi': 'DOI',

   # numeric “*_Value” columns → scalar quantities
   'capacity_value': 'capacity',
   'voltage_value': 'voltage',
   'conductivity_value': 'conductivity',
   'coulombic_efficiency_value': 'coulombic_efficiency',

   # energy-density synonyms
   'energy_value': 'energy_density',
   'energy_raw_value': 'energy_density_raw_value',
   'energy_raw_unit': 'energy_density_raw_unit',
   'energy_unit': 'energy_density_raw_unit',   
 }


def _col_to_attr(column: str) -> str:
    """
    Map CSV/YAML column names → :class:`BatteryDatabase` attributes.
    Keeps the previous *lower-case/underscore* rule but honours explicit
    aliases first.
    """
    key = column.strip().lower().replace(' ', '_')
    return _ALIASES.get(key, key)