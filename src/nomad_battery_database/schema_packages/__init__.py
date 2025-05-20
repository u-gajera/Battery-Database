from nomad.config.models.plugins import SchemaPackageEntryPoint

__all__ = ["battery_schema"]


class BatteryDBSchemaEntryPoint(SchemaPackageEntryPoint):
    """Entry‑point that returns the *battery* schema package instance."""

    def load(self):  # noqa: D401 – NOMAD API
        from .battery import m_package

        return m_package


battery_schema = BatteryDBSchemaEntryPoint(
    name="battery_schema",
    description="Metainfo schema package for curated battery database entries.",
)