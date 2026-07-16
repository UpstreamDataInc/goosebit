from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        -- dedup (model, revision) before adding the unique index; lowest id survives

        -- repoint devices at the surviving row
        UPDATE "device" SET "hardware_id" = (
            SELECT MIN("h2"."id") FROM "hardware" "h2", "hardware" "h1"
            WHERE "h1"."id" = "device"."hardware_id"
              AND "h2"."model" = "h1"."model" AND "h2"."revision" = "h1"."revision"
        ) WHERE "hardware_id" NOT IN (SELECT MIN("id") FROM "hardware" GROUP BY "model", "revision");

        -- drop links that would duplicate after remapping
        DELETE FROM "software_compatibility" WHERE EXISTS (
            SELECT 1 FROM "software_compatibility" "sc2", "hardware" "h1", "hardware" "h2"
            WHERE "h1"."id" = "software_compatibility"."hardware_id"
              AND "h2"."id" = "sc2"."hardware_id"
              AND "sc2"."software_id" = "software_compatibility"."software_id"
              AND "h2"."model" = "h1"."model" AND "h2"."revision" = "h1"."revision"
              AND "sc2"."hardware_id" < "software_compatibility"."hardware_id"
        );
        UPDATE "software_compatibility" SET "hardware_id" = (
            SELECT MIN("h2"."id") FROM "hardware" "h2", "hardware" "h1"
            WHERE "h1"."id" = "software_compatibility"."hardware_id"
              AND "h2"."model" = "h1"."model" AND "h2"."revision" = "h1"."revision"
        ) WHERE "hardware_id" NOT IN (SELECT MIN("id") FROM "hardware" GROUP BY "model", "revision");

        DELETE FROM "hardware" WHERE "id" NOT IN (SELECT MIN("id") FROM "hardware" GROUP BY "model", "revision");

        CREATE UNIQUE INDEX "uid_hardware_model_292e2e" ON "hardware" ("model", "revision");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP INDEX IF EXISTS "uid_hardware_model_292e2e";"""


MODELS_STATE = (
    "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"
)
