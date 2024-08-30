from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    dialect = db.schema_generator.DIALECT

    if dialect == "postgres":
        return """
CREATE TABLE IF NOT EXISTS "hardware" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "model" VARCHAR(255) NOT NULL,
    "revision" VARCHAR(255) NOT NULL
);
CREATE TABLE IF NOT EXISTS "software" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "uri" VARCHAR(255) NOT NULL,
    "size" BIGINT NOT NULL,
    "hash" VARCHAR(255) NOT NULL,
    "version" VARCHAR(255) NOT NULL
);
CREATE TABLE IF NOT EXISTS "device" (
    "uuid" VARCHAR(255) NOT NULL  PRIMARY KEY,
    "name" VARCHAR(255),
    "force_update" BOOL NOT NULL  DEFAULT False,
    "sw_version" VARCHAR(255),
    "feed" VARCHAR(255) NOT NULL  DEFAULT 'default',
    "update_mode" SMALLINT NOT NULL  DEFAULT 3,
    "last_state" SMALLINT NOT NULL  DEFAULT 1,
    "progress" INT,
    "log_complete" BOOL NOT NULL  DEFAULT False,
    "last_log" TEXT,
    "last_seen" BIGINT,
    "last_ip" VARCHAR(15),
    "last_ipv6" VARCHAR(40),
    "assigned_software_id" INT REFERENCES "software" ("id") ON DELETE SET NULL,
    "hardware_id" INT NOT NULL REFERENCES "hardware" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "device"."update_mode" IS 'NONE: 0\nLATEST: 1\nPINNED: 2\nROLLOUT: 3\nASSIGNED: 4';
COMMENT ON COLUMN "device"."last_state" IS 'NONE: 0\nUNKNOWN: 1\nREGISTERED: 2\nRUNNING: 3\nERROR: 4\nFINISHED: 5';
CREATE TABLE IF NOT EXISTS "rollout" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(255),
    "feed" VARCHAR(255) NOT NULL  DEFAULT 'default',
    "paused" BOOL NOT NULL  DEFAULT False,
    "success_count" INT NOT NULL  DEFAULT 0,
    "failure_count" INT NOT NULL  DEFAULT 0,
    "software_id" INT NOT NULL REFERENCES "software" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "tag" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS "software_compatibility" (
    "software_id" INT NOT NULL REFERENCES "software" ("id") ON DELETE CASCADE,
    "hardware_id" INT NOT NULL REFERENCES "hardware" ("id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS "uidx_software_co_softwar_2683cc" ON "software_compatibility" ("software_id", "hardware_id");
CREATE TABLE IF NOT EXISTS "device_tags" (
    "device_id" VARCHAR(255) NOT NULL REFERENCES "device" ("uuid") ON DELETE CASCADE,
    "tag_id" INT NOT NULL REFERENCES "tag" ("id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS "uidx_device_tags_device__2ab77e" ON "device_tags" ("device_id", "tag_id");"""

    else:
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
    "version" VARCHAR(255) NOT NULL
);
CREATE TABLE IF NOT EXISTS "device" (
    "uuid" VARCHAR(255) NOT NULL  PRIMARY KEY,
    "name" VARCHAR(255),
    "force_update" INT NOT NULL  DEFAULT 0,
    "sw_version" VARCHAR(255),
    "feed" VARCHAR(255) NOT NULL  DEFAULT 'default',
    "update_mode" SMALLINT NOT NULL  DEFAULT 3 /* NONE: 0\nLATEST: 1\nPINNED: 2\nROLLOUT: 3\nASSIGNED: 4 */,
    "last_state" SMALLINT NOT NULL  DEFAULT 1 /* NONE: 0\nUNKNOWN: 1\nREGISTERED: 2\nRUNNING: 3\nERROR: 4\nFINISHED: 5 */,
    "progress" INT,
    "log_complete" INT NOT NULL  DEFAULT 0,
    "last_log" TEXT,
    "last_seen" BIGINT,
    "last_ip" VARCHAR(15),
    "last_ipv6" VARCHAR(40),
    "assigned_software_id" INT REFERENCES "software" ("id") ON DELETE SET NULL,
    "hardware_id" INT NOT NULL REFERENCES "hardware" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "rollout" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(255),
    "feed" VARCHAR(255) NOT NULL  DEFAULT 'default',
    "paused" INT NOT NULL  DEFAULT 0,
    "success_count" INT NOT NULL  DEFAULT 0,
    "failure_count" INT NOT NULL  DEFAULT 0,
    "software_id" INT NOT NULL REFERENCES "software" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "tag" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "name" VARCHAR(255) NOT NULL
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
    "device_id" VARCHAR(255) NOT NULL REFERENCES "device" ("uuid") ON DELETE CASCADE,
    "tag_id" INT NOT NULL REFERENCES "tag" ("id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS "uidx_device_tags_device__2ab77e" ON "device_tags" ("device_id", "tag_id");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
