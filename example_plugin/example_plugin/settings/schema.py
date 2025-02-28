from example_plugin.schema import ExamplePluginShow
from goosebit.schema.plugins import PluginSettings


class ExamplePluginSettings(PluginSettings):
    example_plugin_show: list[ExamplePluginShow]
