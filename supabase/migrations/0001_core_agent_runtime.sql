-- Core runtime persistence for agentic-core-template.
-- Supabase is optional infrastructure; FastAPI remains the backend runtime.

create table if not exists public.conversations (
    id text primary key,
    agent_id text not null,
    user_id text,
    title text,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.messages (
    id text primary key,
    conversation_id text not null references public.conversations(id) on delete cascade,
    role text not null,
    content text not null,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create table if not exists public.agent_snapshots (
    id text primary key,
    agent_id text not null,
    conversation_id text not null references public.conversations(id) on delete cascade,
    state jsonb not null default '{}'::jsonb,
    snapshot jsonb,
    version integer not null default 1,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (agent_id, conversation_id)
);

create table if not exists public.skill_runs (
    id text primary key,
    skill_name text not null,
    conversation_id text references public.conversations(id) on delete set null,
    input_data jsonb not null default '{}'::jsonb,
    output_data jsonb,
    status text not null default 'success',
    error text,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create table if not exists public.audit_events (
    id text primary key,
    event_type text not null,
    actor_id text,
    agent_id text,
    conversation_id text references public.conversations(id) on delete set null,
    payload jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create table if not exists public.files (
    id text primary key,
    bucket text not null,
    path text not null,
    owner_id text,
    conversation_id text references public.conversations(id) on delete set null,
    filename text,
    content_type text,
    size_bytes bigint,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    unique (bucket, path)
);

create index if not exists conversations_agent_id_idx on public.conversations(agent_id);
create index if not exists conversations_user_id_idx on public.conversations(user_id);
create index if not exists messages_conversation_id_created_at_idx on public.messages(conversation_id, created_at);
create index if not exists agent_snapshots_conversation_id_idx on public.agent_snapshots(conversation_id);
create index if not exists skill_runs_conversation_id_idx on public.skill_runs(conversation_id);
create index if not exists skill_runs_skill_name_idx on public.skill_runs(skill_name);
create index if not exists audit_events_conversation_id_idx on public.audit_events(conversation_id);
create index if not exists audit_events_event_type_created_at_idx on public.audit_events(event_type, created_at);
create index if not exists files_owner_id_idx on public.files(owner_id);
create index if not exists files_conversation_id_idx on public.files(conversation_id);

alter table public.conversations enable row level security;
alter table public.messages enable row level security;
alter table public.agent_snapshots enable row level security;
alter table public.skill_runs enable row level security;
alter table public.audit_events enable row level security;
alter table public.files enable row level security;

-- The backend service-role client bypasses RLS. Authenticated user policies below
-- are intentionally scoped to owned rows for projects exposing these tables through
-- the Supabase Data API.

create policy "conversations_select_own"
on public.conversations
for select
to authenticated
using (user_id = auth.uid()::text);

create policy "conversations_insert_own"
on public.conversations
for insert
to authenticated
with check (user_id = auth.uid()::text);

create policy "conversations_update_own"
on public.conversations
for update
to authenticated
using (user_id = auth.uid()::text)
with check (user_id = auth.uid()::text);

create policy "messages_select_own_conversation"
on public.messages
for select
to authenticated
using (
    exists (
        select 1
        from public.conversations c
        where c.id = messages.conversation_id
          and c.user_id = auth.uid()::text
    )
);

create policy "messages_insert_own_conversation"
on public.messages
for insert
to authenticated
with check (
    exists (
        select 1
        from public.conversations c
        where c.id = messages.conversation_id
          and c.user_id = auth.uid()::text
    )
);

create policy "agent_snapshots_select_own_conversation"
on public.agent_snapshots
for select
to authenticated
using (
    exists (
        select 1
        from public.conversations c
        where c.id = agent_snapshots.conversation_id
          and c.user_id = auth.uid()::text
    )
);

create policy "agent_snapshots_write_own_conversation"
on public.agent_snapshots
for all
to authenticated
using (
    exists (
        select 1
        from public.conversations c
        where c.id = agent_snapshots.conversation_id
          and c.user_id = auth.uid()::text
    )
)
with check (
    exists (
        select 1
        from public.conversations c
        where c.id = agent_snapshots.conversation_id
          and c.user_id = auth.uid()::text
    )
);

create policy "skill_runs_select_own_conversation"
on public.skill_runs
for select
to authenticated
using (
    conversation_id is not null
    and exists (
        select 1
        from public.conversations c
        where c.id = skill_runs.conversation_id
          and c.user_id = auth.uid()::text
    )
);

create policy "skill_runs_insert_own_conversation"
on public.skill_runs
for insert
to authenticated
with check (
    conversation_id is not null
    and exists (
        select 1
        from public.conversations c
        where c.id = skill_runs.conversation_id
          and c.user_id = auth.uid()::text
    )
);

create policy "audit_events_select_own"
on public.audit_events
for select
to authenticated
using (
    actor_id = auth.uid()::text
    or (
        conversation_id is not null
        and exists (
            select 1
            from public.conversations c
            where c.id = audit_events.conversation_id
              and c.user_id = auth.uid()::text
        )
    )
);

create policy "audit_events_insert_own"
on public.audit_events
for insert
to authenticated
with check (
    actor_id = auth.uid()::text
    or (
        conversation_id is not null
        and exists (
            select 1
            from public.conversations c
            where c.id = audit_events.conversation_id
              and c.user_id = auth.uid()::text
        )
    )
);

create policy "files_select_own"
on public.files
for select
to authenticated
using (owner_id = auth.uid()::text);

create policy "files_insert_own"
on public.files
for insert
to authenticated
with check (owner_id = auth.uid()::text);

create policy "files_update_own"
on public.files
for update
to authenticated
using (owner_id = auth.uid()::text)
with check (owner_id = auth.uid()::text);
