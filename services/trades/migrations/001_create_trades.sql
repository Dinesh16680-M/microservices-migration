-- account_id points to the accounts service. There is no foreign key on purpose:
-- each service owns its own database, so the trades service checks the account over HTTP.
CREATE TABLE trades (
    id         SERIAL PRIMARY KEY,
    account_id INTEGER        NOT NULL,
    isin       CHAR(12)       NOT NULL,
    side       TEXT           NOT NULL CHECK (side IN ('BUY', 'SELL')),
    quantity   INTEGER        NOT NULL CHECK (quantity > 0),
    price      NUMERIC(14, 4) NOT NULL CHECK (price > 0),
    created_at TIMESTAMPTZ    NOT NULL DEFAULT now()
);
