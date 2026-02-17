-- ============================================================
-- Supabase schema for CAD Commander AI Chat
-- Run against your Supabase project via SQL Editor or psql.
-- Requires pgvector extension (enabled by default on Supabase).
-- ============================================================

-- Enable pgvector
create extension if not exists vector with schema extensions;

-- ── Knowledge embeddings ────────────────────────────────────

create table if not exists knowledge_embeddings (
    id          bigint generated always as identity primary key,
    file_path   text not null,
    chunk_index integer not null,
    heading_hierarchy text[] default '{}',
    chunk_text  text not null,
    token_count integer,
    embedding   vector(1536) not null,
    metadata    jsonb default '{}',
    created_at  timestamptz default now(),

    unique (file_path, chunk_index)
);

-- HNSW index for fast cosine similarity search
create index if not exists knowledge_embeddings_embedding_idx
    on knowledge_embeddings
    using ivfflat (embedding vector_cosine_ops)
    with (lists = 100);

-- ── Chat sessions ───────────────────────────────────────────

create table if not exists chat_sessions (
    id              uuid primary key default gen_random_uuid(),
    consent_given   boolean not null default false,
    created_at      timestamptz default now(),
    last_active_at  timestamptz default now(),
    user_agent      text
);

-- ── Chat messages ───────────────────────────────────────────

create table if not exists chat_messages (
    id                uuid primary key default gen_random_uuid(),
    session_id        uuid not null references chat_sessions(id) on delete cascade,
    role              text not null check (role in ('user', 'assistant')),
    content           text not null,
    context_chunks    jsonb,
    model             text,
    prompt_tokens     integer,
    completion_tokens integer,
    created_at        timestamptz default now()
);

create index if not exists chat_messages_session_idx
    on chat_messages (session_id, created_at);

-- ── Feedback ────────────────────────────────────────────────

create table if not exists feedback (
    id          uuid primary key default gen_random_uuid(),
    message_id  uuid not null unique references chat_messages(id) on delete cascade,
    session_id  uuid not null references chat_sessions(id) on delete cascade,
    rating      text not null check (rating in ('up', 'down')),
    comment     text,
    created_at  timestamptz default now()
);

-- ── RPC: match_knowledge ────────────────────────────────────
-- Performs cosine similarity search on knowledge_embeddings.

create or replace function match_knowledge(
    query_embedding vector(1536),
    match_threshold float default 0.7,
    match_count int default 6
)
returns table (
    file_path         text,
    chunk_index       integer,
    chunk_text        text,
    heading_hierarchy text[],
    metadata          jsonb,
    similarity        float
)
language sql stable
as $$
    select
        ke.file_path,
        ke.chunk_index,
        ke.chunk_text,
        ke.heading_hierarchy,
        ke.metadata,
        1 - (ke.embedding <=> query_embedding) as similarity
    from knowledge_embeddings ke
    where 1 - (ke.embedding <=> query_embedding) > match_threshold
    order by ke.embedding <=> query_embedding
    limit match_count;
$$;

-- ── View: highly_rated_qa ───────────────────────────────────
-- Joins feedback(up) → assistant message → preceding user message
-- to provide few-shot examples for the RAG pipeline.

create or replace view highly_rated_qa as
select
    user_msg.content as question,
    asst_msg.content as answer
from feedback f
join chat_messages asst_msg on asst_msg.id = f.message_id
join lateral (
    select cm.content
    from chat_messages cm
    where cm.session_id = asst_msg.session_id
      and cm.role = 'user'
      and cm.created_at < asst_msg.created_at
    order by cm.created_at desc
    limit 1
) user_msg on true
where f.rating = 'up'
order by f.created_at desc;
