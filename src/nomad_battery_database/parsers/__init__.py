from nomad.config.models.plugins import ParserEntryPoint
from pydantic import Field


class BatteryDBParserEntryPoint(ParserEntryPoint):
    """Entry‑point for the battery CSV/YAML parser."""

    # Allow overriding the regex via `pyproject.toml` if desired
    mainfile_name_re: str | None = Field(
            default=r".*\.extracted_battery\.(csv|ya?ml)$",
            description="Regex to match mainfiles.",
        )

    def load(self): 
        from .battery_parser import BatteryParser  # noqa: E402
        return BatteryParser(**self.dict())


battery_db_parser = BatteryDBParserEntryPoint(  
    name='battery_parser',
    description="Parser for curated battery database CSV and YAML files.",
)