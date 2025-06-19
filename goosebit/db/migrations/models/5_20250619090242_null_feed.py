from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    dialect = db.schema_generator.DIALECT

    if dialect == "postgres":
        return """
            ALTER TABLE "device" ALTER COLUMN "feed" DROP NOT NULL;"""

    return """PRAGMA foreign_keys=off;

    CREATE TABLE "device_new" (
        "id" CHAR(255) NOT NULL PRIMARY KEY,
        "name" CHAR(255),
        "assigned_software_id" INT,
        "force_update" INT NOT NULL DEFAULT 0,
        "sw_version" CHAR(255),
        "hardware_id" INT NOT NULL,
        "feed" CHAR(255) DEFAULT 'default',  -- NULL allowed here
        "update_mode" INT NOT NULL DEFAULT 0,
        "last_state" INT NOT NULL DEFAULT 0,
        "progress" INT,
        "last_log" TEXT,
        "last_seen" BIGINT,
        "last_ip" CHAR(15),
        "last_ipv6" CHAR(40),
        "auth_token" CHAR(32)
    );

    INSERT INTO "device_new" SELECT
        id, name, assigned_software_id, force_update, sw_version,
        hardware_id, feed, update_mode, last_state, progress,
        last_log, last_seen, last_ip, last_ipv6, auth_token
    FROM "device";

    DROP TABLE "device";

    ALTER TABLE "device_new" RENAME TO "device";

    PRAGMA foreign_keys=on;
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    dialect = db.schema_generator.DIALECT

    if dialect == "postgres":
        return """
            ALTER TABLE "device" ALTER COLUMN "feed" SET NOT NULL;"""

    return """PRAGMA foreign_keys=off;

    CREATE TABLE "device_old" (
        "id" CHAR(255) NOT NULL PRIMARY KEY,
        "name" CHAR(255),
        "assigned_software_id" INT,
        "force_update" INT NOT NULL DEFAULT 0,
        "sw_version" CHAR(255),
        "hardware_id" INT NOT NULL,
        "feed" CHAR(255) NOT NULL DEFAULT 'default',  -- NOT NULL again
        "update_mode" INT NOT NULL DEFAULT 0,
        "last_state" INT NOT NULL DEFAULT 0,
        "progress" INT,
        "last_log" TEXT,
        "last_seen" BIGINT,
        "last_ip" CHAR(15),
        "last_ipv6" CHAR(40),
        "auth_token" CHAR(32)
    );

    INSERT INTO "device_old" SELECT
        id, name, assigned_software_id, force_update, sw_version,
        hardware_id, feed, update_mode, last_state, progress,
        last_log, last_seen, last_ip, last_ipv6, auth_token
    FROM "device";

    DROP TABLE "device";

    ALTER TABLE "device_old" RENAME TO "device";

    PRAGMA foreign_keys=on;
    """
