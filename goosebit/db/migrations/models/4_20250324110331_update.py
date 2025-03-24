from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "user" (
    "username" VARCHAR(255) NOT NULL  PRIMARY KEY,
    "hashed_pwd" VARCHAR(255) NOT NULL,
    "permissions" JSON NOT NULL,
    "enabled" INT NOT NULL  DEFAULT 1
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "user";"""
