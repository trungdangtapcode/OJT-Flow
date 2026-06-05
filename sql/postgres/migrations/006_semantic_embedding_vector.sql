-- Move retrieval vector storage from deterministic hash dimensions to the
-- semantic embedding dimension used by the default OpenAI/BGE-small setup.

do $$
begin
    if exists (select 1 from pg_type where typname = 'vector') then
        execute 'drop index if exists ojtflow.idx_knowledge_chunks_embedding_hnsw';
        execute 'alter table ojtflow.knowledge_chunks drop column if exists embedding';
        execute 'alter table ojtflow.knowledge_chunks add column embedding vector(384)';
        execute 'create index if not exists idx_knowledge_chunks_embedding_hnsw on ojtflow.knowledge_chunks using hnsw (embedding vector_cosine_ops)';
    end if;
end $$;
