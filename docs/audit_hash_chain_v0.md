# Audit Hash Chain v0

OJTFlow writes every generic audit record with deterministic hash-chain fields:

- `chain_scope`: independent chain partition, currently `owner_user:<user_id>` or `owner_user:system`.
- `chain_sequence`: monotonic sequence within the chain scope.
- `previous_record_hash`: SHA-256 hash of the previous scoped record, or `null` for the first record.
- `record_hash`: SHA-256 hash of the canonical audit record payload excluding `record_hash`.
- `hash_algorithm`: currently `sha256`.
- `chain_status`: `linked` after repository append.

The chain is computed inside the storage repository append path, not in API
handlers. This keeps Assistant/MCP audit records and future audit producers on
the same persistence boundary.

## Deployment Policy

Hash-chain fields are always written. `OJT_AUDIT_HASH_CHAIN_REQUIRED=true`
marks a deployment as requiring chained audit records. Pilot and production
product modes are treated as chain-required even if the flag is not set:

```env
OJT_AUDIT_HASH_CHAIN_REQUIRED=true
```

`GET /api/v1/runtime/config` exposes sanitized audit facts:

- `audit.hash_chain_written`
- `audit.hash_chain_required`
- `audit.hash_chain_required_configured`

## Storage

SQLite self-heals the audit table with nullable chain columns for local and
test deployments. Postgres migration `018_audit_hash_chain.sql` adds mirrored
columns and indexes for chain-scope/sequence verification and record-hash
lookup.

The authoritative record remains `record_json`, which includes the chain fields.
Mirrored SQL columns are for efficient integrity checks and future export/report
queries.

## Limitations

v0 links new records going forward. Existing records that were written before
F130 do not have `record_hash`; the first new record after upgrade starts a new
linked sequence for that owner scope. Full historical backfill and a dedicated
chain verification endpoint are left for a later compliance-hardening pass.
