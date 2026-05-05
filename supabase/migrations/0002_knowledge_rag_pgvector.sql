-- Optional RAG persistence for agentic-core-template.
-- Uses Supabase Postgres + pgvector while keeping agents decoupled from Supabase.

create extension if not exists vector with schema extensions;

create table if not exists public.knowledge_documents (
    id text primary key,
    owner_id text,
    title text,
    source text,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.knowledge_chunks (
    id text primary key,
    document_id text not null references public.knowledge_documents(id) on delete cascade,
    owner_id text,
    content text not null,
    chunk_index integer not null,
    embedding vector(1536) not null,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create index if not exists knowledge_documents_owner_id_idx
on public.knowledge_documents(owner_id);

create index if not exists knowledge_chunks_document_id_idx
on public.knowledge_chunks(document_id);

create index if not exists knowledge_chunks_owner_id_idx
on public.knowledge_chunks(owner_id);

create index if not exists knowledge_chunks_embedding_idx
on public.knowledge_chunks
using ivfflat (embedding vector_cosine_ops)
with (lists = 100);

alter table public.knowledge_documents enable row level security;
alter table public.knowledge_chunks enable row level security;

-- The backend service-role client bypasses RLS. Authenticated user policies
-- below are baseline ownership policies for projects exposing these tables
-- through the Supabase Data API.

create policy "knowledge_documents_select_own"
on public.knowledge_documents
for select
to authenticated
using (owner_id = auth.uid()::text);

create policy "knowledge_documents_insert_own"
on public.knowledge_documents
for insert
to authenticated
with check (owner_id = auth.uid()::text);

create policy "knowledge_documents_update_own"
on public.knowledge_documents
for update
to authenticated
using (owner_id = auth.uid()::text)
with check (owner_id = auth.uid()::text);

create policy "knowledge_documents_delete_own"
on public.knowledge_documents
for delete
to authenticated
using (owner_id = auth.uid()::text);

create policy "knowledge_chunks_select_own"
on public.knowledge_chunks
for select
to authenticated
using (owner_id = auth.uid()::text);

create policy "knowledge_chunks_insert_own"
on public.knowledge_chunks
for insert
to authenticated
with check (owner_id = auth.uid()::text);

create policy "knowledge_chunks_update_own"
on public.knowledge_chunks
for update
to authenticated
using (owner_id = auth.uid()::text)
with check (owner_id = auth.uid()::text);

create policy "knowledge_chunks_delete_own"
on public.knowledge_chunks
for delete
to authenticated
using (owner_id = auth.uid()::text);

create or replace function public.match_knowledge_chunks(
    query_embedding vector(1536),
    match_count integer default 5,
    similarity_threshold double precision default 0.2,
    filter_owner_id text default null
)
returns table (
    document_id text,
    chunk_id text,
    content text,
    similarity double precision,
    metadata jsonb
)
language sql
stable
as $$
    select
        kc.document_id,
        kc.id as chunk_id,
        kc.content,
        1 - (kc.embedding <=> query_embedding) as similarity,
        kc.metadata
    from public.knowledge_chunks kc
    where (filter_owner_id is null or kc.owner_id = filter_owner_id)
      and 1 - (kc.embedding <=> query_embedding) >= similarity_threshold
    order by kc.embedding <=> query_embedding
    limit match_count;
$$;
