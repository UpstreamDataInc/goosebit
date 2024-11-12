from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "device" ADD "auth_token" VARCHAR(32);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "device" DROP COLUMN "auth_token";"""
