from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "device" DROP COLUMN "log_complete";"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "device" ADD "log_complete" INT NOT NULL  DEFAULT 0;"""


MODELS_STATE = (
    "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"
)
