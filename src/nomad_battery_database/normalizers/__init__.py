from nomad_battery_database.normalizers.normalizer import BatteryNormalizer

__all__ = ["BatteryNormalizer"]

class NewNormalizerEntryPoint(NormalizerEntryPoint):
    parameter: int = Field(0, description='Custom configuration parameter')

    def load(self):
        return BatteryNormalizer()
