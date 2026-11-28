from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "software" ADD "update_timeout" INT NOT NULL  DEFAULT 600;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "software" DROP COLUMN "update_timeout";"""


MODELS_STATE = (
    "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"
)
