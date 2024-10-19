from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "device" DROP COLUMN "last_ip";
        ALTER TABLE "device" DROP COLUMN "last_ipv6";"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "device" ADD "last_ip" VARCHAR(15);
        ALTER TABLE "device" ADD "last_ipv6" VARCHAR(40);"""
