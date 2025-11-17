from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "software" ADD "image_format" SMALLINT NOT NULL  DEFAULT 0 /* SWU: 0
RAUC: 1 */;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "software" DROP COLUMN "image_format";"""


MODELS_STATE = (
    "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"
    "QwrQsj22XHRLblrldy51mru96qe3n9Dz/45b0="
)
