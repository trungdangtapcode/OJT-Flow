alter table ojtflow.audit_records
    add column if not exists chain_scope text,
    add column if not exists chain_sequence bigint,
    add column if not exists previous_record_hash text,
    add column if not exists record_hash text,
    add column if not exists hash_algorithm text,
    add column if not exists chain_status text not null default 'pending';

alter table ojtflow.audit_records
    add constraint audit_records_chain_status_check
    check (chain_status in ('pending', 'linked')) not valid;

alter table ojtflow.audit_records
    add constraint audit_records_record_hash_sha256_check
    check (record_hash is null or record_hash ~ '^[a-f0-9]{64}$') not valid;

alter table ojtflow.audit_records
    add constraint audit_records_previous_record_hash_sha256_check
    check (
        previous_record_hash is null
        or previous_record_hash ~ '^[a-f0-9]{64}$'
    ) not valid;

create index if not exists idx_audit_records_chain_scope_sequence
    on ojtflow.audit_records(chain_scope, chain_sequence desc);

create unique index if not exists idx_audit_records_chain_scope_record_hash
    on ojtflow.audit_records(chain_scope, record_hash)
    where record_hash is not null;
