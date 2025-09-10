from nomad.config.models.plugins import SchemaPackageEntryPoint

from .battery_schema import m_package


class BatteryDBSchemaEntryPoint(SchemaPackageEntryPoint):
    """Entry‑point that returns the *battery* schema package instance."""

    def load(self):  # noqa: D401 – NOMAD API
        return m_package


battery_schema = BatteryDBSchemaEntryPoint(
    name="battery_schema",
    description="Metainfo schema package for curated battery database entries.",
)