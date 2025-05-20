from pydantic import Field
from nomad.config.models.plugins import ParserEntryPoint

__all__ = ["battery_db_parser"]


class BatteryDBParserEntryPoint(ParserEntryPoint):
    """Entry‑point for the battery CSV/YAML parser."""

    # Allow overriding the regex via `pyproject.toml` if desired
    mainfile_name_re: str | None = Field(default=r".*\.(csv|ya?ml)$", description="Regex to match mainfiles.")

    def load(self):  # noqa: D401 – NOMAD API signature
        from .battery_db import BatteryParser  # local import to avoid heavy deps at import time

        # Pass any configured Pydantic fields to the parser constructor
        return BatteryParser(**self.dict())


battery_db_parser = BatteryDBParserEntryPoint(  # noqa: N818 – plugin convention
    name="battery_db",
    description="Parser for curated battery database CSV and YAML files.",
)