CREATE TABLE IF NOT EXISTS version (version TEXT PRIMARY KEY);
INSERT INTO version (version) VALUES ('v3.6') ON CONFLICT (version) DO NOTHING;
CREATE TABLE IF NOT EXISTS plugins (plugin TEXT PRIMARY KEY, version TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS message_persistence (server_name TEXT NOT NULL, embed_name TEXT NOT NULL, embed BIGINT NOT NULL, PRIMARY KEY (server_name, embed_name));
CREATE TABLE IF NOT EXISTS nodes (guild_id BIGINT NOT NULL, node TEXT NOT NULL, master BOOLEAN NOT NULL, last_seen TIMESTAMP DEFAULT NOW(), PRIMARY KEY (guild_id, node));
CREATE TABLE IF NOT EXISTS instances (node TEXT NOT NULL, instance TEXT NOT NULL, port BIGINT NOT NULL, server_name TEXT, last_seen TIMESTAMP DEFAULT NOW(), PRIMARY KEY(node, instance));
CREATE UNIQUE INDEX IF NOT EXISTS idx_instances ON instances (node, port);
CREATE UNIQUE INDEX IF NOT EXISTS idx_instances_server_name ON instances (server_name);
CREATE TABLE IF NOT EXISTS servers (server_name TEXT PRIMARY KEY, blue_password TEXT, red_password TEXT, maintenance BOOLEAN NOT NULL DEFAULT FALSE);
CREATE TABLE IF NOT EXISTS intercom (id SERIAL PRIMARY KEY, node TEXT NOT NULL, time TIMESTAMP NOT NULL DEFAULT NOW(), data JSON, priority INTEGER NOT NULL DEFAULT 0);
CREATE INDEX IF NOT EXISTS idx_intercom_node ON intercom (node);
CREATE TABLE IF NOT EXISTS files (id SERIAL PRIMARY KEY, name TEXT NOT NULL, data BYTEA NOT NULL, created TIMESTAMP NOT NULL DEFAULT NOW());
CREATE TABLE IF NOT EXISTS audit(id SERIAL PRIMARY KEY, node TEXT NOT NULL, event TEXT NOT NULL, server_name TEXT, discord_id BIGINT, ucid TEXT, time TIMESTAMP NOT NULL DEFAULT NOW());
