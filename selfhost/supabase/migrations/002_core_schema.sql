-- Étape 7 — Schéma PostgreSQL principal OSS+
-- Équivalent des collections Firestore : conversations, memories, action_items, people
-- À exécuter après 001_profiles.sql dans l'éditeur SQL Supabase.

-- ============================================================
-- CONVERSATIONS
-- ============================================================
create table if not exists public.conversations (
    id         text        not null,
    uid        uuid        not null references public.profiles(id) on delete cascade,
    created_at timestamptz default now() not null,
    started_at timestamptz,
    finished_at timestamptz,
    -- transcript_segments : liste de segments JSON [{speaker, text, start, end, …}]
    transcript_segments jsonb   default '[]' not null,
    summary    text,
    overview   text,
    title      text,
    emoji      text,
    category   text,
    status     text        default 'completed',
    source     text,
    language   text,
    -- structured : {title, overview, emoji, category, action_items, events}
    structured jsonb,
    -- apps_response : [{app_id, content}]
    apps_response jsonb    default '[]',
    discarded  boolean     default false not null,
    deleted    boolean     default false not null,
    geolocation jsonb,
    postprocessing jsonb,
    primary key (uid, id)
);

create index if not exists conversations_uid_created_at
    on public.conversations (uid, created_at desc);

alter table public.conversations enable row level security;

create policy "conversations_select_own"
    on public.conversations for select
    using (auth.uid() = uid);

create policy "conversations_insert_own"
    on public.conversations for insert
    with check (auth.uid() = uid);

create policy "conversations_update_own"
    on public.conversations for update
    using (auth.uid() = uid);

create policy "conversations_delete_own"
    on public.conversations for delete
    using (auth.uid() = uid);

-- ============================================================
-- MEMORIES
-- ============================================================
create table if not exists public.memories (
    id         text        not null,
    uid        uuid        not null references public.profiles(id) on delete cascade,
    content    text        not null,
    category   text        default 'interesting',
    visibility text        default 'private',
    tags       jsonb       default '[]',
    headline   text,
    created_at timestamptz default now() not null,
    updated_at timestamptz default now() not null,
    deleted    boolean     default false not null,
    manual     boolean     default false not null,
    scoring    jsonb,
    primary key (uid, id)
);

create index if not exists memories_uid_created_at
    on public.memories (uid, created_at desc);

alter table public.memories enable row level security;

create policy "memories_select_own"
    on public.memories for select
    using (auth.uid() = uid);

create policy "memories_insert_own"
    on public.memories for insert
    with check (auth.uid() = uid);

create policy "memories_update_own"
    on public.memories for update
    using (auth.uid() = uid);

create policy "memories_delete_own"
    on public.memories for delete
    using (auth.uid() = uid);

-- ============================================================
-- ACTION ITEMS
-- ============================================================
create table if not exists public.action_items (
    id              text        not null,
    uid             uuid        not null references public.profiles(id) on delete cascade,
    content         text        not null,
    completed       boolean     default false not null,
    created_at      timestamptz default now() not null,
    updated_at      timestamptz default now() not null,
    due_at          timestamptz,
    completed_at    timestamptz,
    deleted         boolean     default false not null,
    conversation_id text,
    primary key (uid, id)
);

create index if not exists action_items_uid_created_at
    on public.action_items (uid, created_at desc);

alter table public.action_items enable row level security;

create policy "action_items_select_own"
    on public.action_items for select
    using (auth.uid() = uid);

create policy "action_items_insert_own"
    on public.action_items for insert
    with check (auth.uid() = uid);

create policy "action_items_update_own"
    on public.action_items for update
    using (auth.uid() = uid);

create policy "action_items_delete_own"
    on public.action_items for delete
    using (auth.uid() = uid);

-- ============================================================
-- PEOPLE  (profils de voix pour la diarization)
-- ============================================================
create table if not exists public.people (
    id                       text        not null,
    uid                      uuid        not null references public.profiles(id) on delete cascade,
    name                     text        not null,
    created_at               timestamptz default now() not null,
    updated_at               timestamptz default now() not null,
    speech_samples           jsonb       default '[]',
    speech_sample_transcripts jsonb      default '[]',
    speech_samples_version   int         default 1,
    speaker_embedding        jsonb,
    primary key (uid, id)
);

alter table public.people enable row level security;

create policy "people_select_own"
    on public.people for select
    using (auth.uid() = uid);

create policy "people_insert_own"
    on public.people for insert
    with check (auth.uid() = uid);

create policy "people_update_own"
    on public.people for update
    using (auth.uid() = uid);

create policy "people_delete_own"
    on public.people for delete
    using (auth.uid() = uid);
