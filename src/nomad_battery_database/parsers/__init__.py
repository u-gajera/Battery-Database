from nomad_battery_database.parsers.parser import BatteryParser

__all__ = ["BatteryParser"]

class NewParserEntryPoint(ParserEntryPoint):
    parameter: int = Field(0, description='Custom configuration parameter')

    def load(self):
        return BatteryParser()
