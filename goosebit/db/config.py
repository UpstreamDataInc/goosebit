from goosebit.settings import config

SQLMODEL_CONFIG = {"url": config.db_uri, "connect_args": {"check_same_thread": False}}
