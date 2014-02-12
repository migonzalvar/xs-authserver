PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS users (
    uuid VARCHAR(36) NOT NULL,
    nickname VARCHAR(200) NOT NULL,
    pkey_hash VARCHAR(40) NOT NULL,
    PRIMARY KEY (uuid),
    UNIQUE (pkey_hash)
);
COMMIT;
