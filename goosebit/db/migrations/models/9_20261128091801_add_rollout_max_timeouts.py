from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "rollout" ADD "max_timeouts" INT;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "rollout" DROP COLUMN "max_timeouts";"""


MODELS_STATE = (
    "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"
)
