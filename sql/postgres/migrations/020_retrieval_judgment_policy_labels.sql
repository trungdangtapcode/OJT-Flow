-- Expand retrieval judgment labels beyond relevance-only values.

alter table if exists ojtflow.retrieval_relevance_judgments
    drop constraint if exists retrieval_judgments_value_check;

alter table if exists ojtflow.retrieval_relevance_judgments
    add constraint retrieval_judgments_value_check
        check (
            value in (
                'relevant',
                'partial',
                'irrelevant',
                'not_relevant',
                'unsafe',
                'stale',
                'source_policy_blocked'
            )
        );
