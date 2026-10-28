-- Runs once when the Postgres container starts with an empty volume.
-- One database per service: each service owns its data.
CREATE DATABASE accounts;
CREATE DATABASE trades;
