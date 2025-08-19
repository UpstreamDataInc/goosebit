from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "software" ADD "image_format" SMALLINT NOT NULL  DEFAULT 0 /* SWU: 0\nRAUC: 1 */;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "software" DROP COLUMN "image_format";"""
