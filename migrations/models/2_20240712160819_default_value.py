from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "device" ADD "new_last_state" VARCHAR(255)   DEFAULT 'unknown';
        UPDATE "device" SET "new_last_state" = COALESCE("last_state", 'unknown');
        ALTER TABLE "device" DROP "last_state";
        ALTER TABLE "device" RENAME COLUMN "new_last_state" TO "last_state";"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "device" ADD "old_last_state" VARCHAR(255);
        UPDATE "device" SET "old_last_state" = "last_state";
        ALTER TABLE "device" DROP "last_state";
        ALTER TABLE "device" RENAME COLUMN "old_last_state" TO "last_state";"""
