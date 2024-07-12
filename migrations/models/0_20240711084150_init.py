from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "device" (
    "uuid" VARCHAR(255) NOT NULL  PRIMARY KEY,
    "name" VARCHAR(255),
    "fw_file" VARCHAR(255) NOT NULL  DEFAULT 'latest',
    "fw_version" VARCHAR(255),
    "last_state" VARCHAR(255),
    "last_log" TEXT,
    "last_seen" BIGINT,
    "last_ip" VARCHAR(15),
    "last_ipv6" VARCHAR(40)
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
CREATE TABLE IF NOT EXISTS "device_tags" (
    "device_id" VARCHAR(255) NOT NULL REFERENCES "device" ("uuid") ON DELETE CASCADE,
    "tag_id" INT NOT NULL REFERENCES "tag" ("id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS "uidx_device_tags_device__2ab77e" ON "device_tags" ("device_id", "tag_id");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
