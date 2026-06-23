-- Record how a user authenticated (e.g. "keycloak", "google") when Keycloak is the
-- OIDC authority that brokers local and federated identities.

alter table ojtflow.users
    add column if not exists identity_provider text;
