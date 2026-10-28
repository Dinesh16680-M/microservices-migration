-- Listing trades per account is the most common query.
CREATE INDEX idx_trades_account_id ON trades (account_id);
