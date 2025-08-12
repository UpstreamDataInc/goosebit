from goosebit.schema.plugins import PluginSchema

from . import middleware

config = PluginSchema(
    middleware=middleware.ForwardedHeaderMiddleware,
)
