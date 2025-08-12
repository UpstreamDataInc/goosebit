from goosebit_simple_stats.schema import SimpleStatsShow

from goosebit.schema.plugins import PluginSettings


class SimpleStatsSettings(PluginSettings):
    simple_stats_show: list[SimpleStatsShow]
