from nomad.config.models.plugins import ParserEntryPoint


class BatteryDBParserEntryPoint(ParserEntryPoint):

    def load(self): 
        from .battery_parser import BatteryParser  # noqa: E402, PLC0415

        return BatteryParser(**self.dict())


battery_db_parser = BatteryDBParserEntryPoint(  
    name='battery_parser',
    description="Parser for curated battery database CSV and YAML files.",
    mainfile_name_re=r'.*\.extracted_battery\.(csv|xlsx?)$',
)