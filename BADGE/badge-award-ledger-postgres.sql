-- TAKY Badge Award Ledger. Apply ONLY in a separately approved database migration.
-- No table, role, credential, or live Netlify environment is created by this file.
-- family/child/badge constitute the scoped aggregate, and one DB transaction
-- locks its head row while writing both the new immutable event and checkpoint.
CREATE TABLE IF NOT EXISTS taky_badge_award_head (
  family_id text NOT NULL CHECK (length(family_id) BETWEEN 1 AND 128),
  child_id text NOT NULL CHECK (length(child_id) BETWEEN 1 AND 128),
  badge_id text NOT NULL CHECK (length(badge_id) BETWEEN 1 AND 128),
  award_count bigint NOT NULL DEFAULT 0 CHECK (award_count >= 0),
  checkpoint char(64) NOT NULL CHECK (checkpoint ~ '^[0-9a-f]{64}$'),
  PRIMARY KEY (family_id,child_id,badge_id)
);

CREATE TABLE IF NOT EXISTS taky_badge_award_event (
  family_id text NOT NULL,
  child_id text NOT NULL,
  badge_id text NOT NULL,
  ledger_sequence bigint NOT NULL CHECK (ledger_sequence >= 0),
  decision_id text NOT NULL CHECK (length(decision_id) > 0),
  award_id char(64) NOT NULL CHECK (award_id ~ '^[0-9a-f]{64}$'),
  -- TEXT rather than JSONB deliberately preserves the HMAC-signed canonical
  -- JSON byte representation and property ordering used by the existing ledger.
  record_json text NOT NULL CHECK (length(record_json) > 0 AND record_json IS JSON),
  digest char(64) NOT NULL CHECK (digest ~ '^[0-9a-f]{64}$'),
  PRIMARY KEY (family_id,child_id,badge_id,ledger_sequence),
  UNIQUE (family_id,child_id,badge_id,decision_id),
  UNIQUE (family_id,child_id,badge_id,award_id),
  FOREIGN KEY (family_id,child_id,badge_id)
    REFERENCES taky_badge_award_head(family_id,child_id,badge_id)
    ON DELETE RESTRICT
);

-- Application credentials should have SELECT/INSERT on immutable events,
-- SELECT/INSERT/UPDATE ONLY on aggregate heads, and NO DELETE/TRUNCATE or
-- UPDATE on event rows; migration credentials remain separately managed.
-- SQL privileges, audited backups, a separate high-watermark/anti-rollback
-- anchor, and row-level security must be configured per actual tenancy.
