from nomad.config.models.plugins import SchemaPackageEntryPoint


class BatterySchemaEntryPoint(SchemaPackageEntryPoint):
    def load(self):
        from nomad_battery_database.schema_packages.schema_package import m_package

        return m_package


schema = BatterySchemaEntryPoint(
    name='NOMAD Battery Schema',
    description='A module containing schemas for the NOMAD battery database.',
)