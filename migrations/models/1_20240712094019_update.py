from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "device" ADD "hw_revision" VARCHAR(255)   DEFAULT 'default';
        ALTER TABLE "device" ADD "hw_model" VARCHAR(255)   DEFAULT 'default';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "device" DROP COLUMN "hw_revision";
        ALTER TABLE "device" DROP COLUMN "hw_model";"""
