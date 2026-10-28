-- Keeps the old SQLite id, so trades from the legacy system can be mapped to the new account.
ALTER TABLE accounts ADD COLUMN legacy_id INTEGER UNIQUE;
