from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    timestamp_type = "TIMESTAMPTZ" if db.schema_generator.DIALECT == "postgres" else "TIMESTAMP"
    # Leave existing entries NULL: their original upload times are unknown.
    return f'ALTER TABLE "software" ADD "created_at" {timestamp_type};'


async def downgrade(db: BaseDBAsyncClient) -> str:
    return 'ALTER TABLE "software" DROP COLUMN "created_at";'


MODELS_STATE = (
    "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"
)
