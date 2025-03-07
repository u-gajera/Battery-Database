from nomad_battery_database.schema_packages.schema_package import m_package

__all__ = ["m_package"]

class NewSchemaPackageEntryPoint(SchemaPackageEntryPoint):
    parameter: int = Field(0, description='Custom configuration parameter')

    def load(self):
        return m_package
