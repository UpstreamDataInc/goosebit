from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "hardware" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "model" VARCHAR(255) NOT NULL,
    "revision" VARCHAR(255) NOT NULL
);
CREATE TABLE IF NOT EXISTS "software" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "uri" VARCHAR(255) NOT NULL,
    "size" BIGINT NOT NULL,
    "hash" VARCHAR(255) NOT NULL,
    "version" VARCHAR(255) NOT NULL,
    "image_format" SMALLINT NOT NULL DEFAULT 0 /* SWU: 0\nRAUC: 1 */
);
CREATE TABLE IF NOT EXISTS "device" (
    "id" VARCHAR(255) NOT NULL PRIMARY KEY,
    "name" VARCHAR(255),
    "force_update" INT NOT NULL DEFAULT 0,
    "sw_version" VARCHAR(255),
    "feed" VARCHAR(255) DEFAULT 'default',
    "update_mode" SMALLINT NOT NULL DEFAULT 3 /* NONE: 0\nLATEST: 1\nPINNED: 2\nROLLOUT: 3\nASSIGNED: 4 */,
    "last_state" SMALLINT NOT NULL DEFAULT 1 /* NONE: 0\nUNKNOWN: 1\nREGISTERED: 2\nRUNNING: 3\nERROR: 4\nFINISHED: 5 */,
    "progress" INT,
    "last_log" TEXT,
    "last_seen" BIGINT,
    "last_ip" VARCHAR(15),
    "last_ipv6" VARCHAR(40),
    "auth_token" VARCHAR(32),
    "assigned_software_id" INT REFERENCES "software" ("id") ON DELETE SET NULL,
    "hardware_id" INT NOT NULL REFERENCES "hardware" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "rollout" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(255),
    "feed" VARCHAR(255) NOT NULL DEFAULT 'default',
    "paused" INT NOT NULL DEFAULT 0,
    "success_count" INT NOT NULL DEFAULT 0,
    "failure_count" INT NOT NULL DEFAULT 0,
    "software_id" INT NOT NULL REFERENCES "software" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_rollout_softwar_3614e1" ON "rollout" ("software_id");
CREATE TABLE IF NOT EXISTS "tag" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "name" VARCHAR(255) NOT NULL
);
CREATE TABLE IF NOT EXISTS "user" (
    "username" VARCHAR(255) NOT NULL PRIMARY KEY,
    "hashed_pwd" VARCHAR(255) NOT NULL,
    "permissions" JSON NOT NULL,
    "enabled" INT NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSON NOT NULL
);
CREATE TABLE IF NOT EXISTS "software_compatibility" (
    "software_id" INT NOT NULL REFERENCES "software" ("id") ON DELETE CASCADE,
    "hardware_id" INT NOT NULL REFERENCES "hardware" ("id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS "uidx_software_co_softwar_2683cc" ON "software_compatibility" ("software_id", "hardware_id");
CREATE TABLE IF NOT EXISTS "device_tags" (
    "device_id" VARCHAR(255) NOT NULL REFERENCES "device" ("id") ON DELETE CASCADE,
    "tag_id" INT NOT NULL REFERENCES "tag" ("id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS "uidx_device_tags_device__2ab77e" ON "device_tags" ("device_id", "tag_id");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "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"
    "46IbJ9R72Rfc6bOuqdOpaX/wA0muEb"
)
