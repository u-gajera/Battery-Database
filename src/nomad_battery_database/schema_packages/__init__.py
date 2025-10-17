from nomad.config.models.plugins import SchemaPackageEntryPoint


class BatteryDBSchemaEntryPoint(SchemaPackageEntryPoint):
    """Entry‑point that returns the *battery* schema package instance."""

    def load(self):
        from nomad_battery_database.schema_packages.battery_schema import m_package
        return m_package


battery_schema = BatteryDBSchemaEntryPoint(
    name="battery_schema",
    description="Metainfo schema package for curated battery database entries.",
)