from nomad.config.models.plugins import ParserEntryPoint


class BatteryParserEntryPoint(ParserEntryPoint):

    def load(self):
        from nomad_battery_database.parsers.parser import BatteryParser

        return BatteryParser()


battery_parser = BatteryParserEntryPoint(
    name='BatteryParser',
    description='Parse excel files containing battery data from publications.',
    mainfile_name_re=r'.+\.xlsx',
    mainfile_mime_re='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    mainfile_contents_dict={
        'Sheet1': {
            '__has_all_keys': [
                'some_key_1',
            ]
        },
    },
)

