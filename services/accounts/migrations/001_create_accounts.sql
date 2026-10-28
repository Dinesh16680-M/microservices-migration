CREATE TABLE accounts (
    id         SERIAL PRIMARY KEY,
    owner      TEXT        NOT NULL,
    currency   CHAR(3)     NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
