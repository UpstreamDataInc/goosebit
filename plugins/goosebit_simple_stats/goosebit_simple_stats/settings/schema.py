from goosebit.schema.plugins import PluginSettings
from goosebit_simple_stats.schema import SimpleStatsShow


class SimpleStatsSettings(PluginSettings):
    simple_stats_show: list[SimpleStatsShow]
