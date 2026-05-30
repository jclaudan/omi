-- Étape 15 (chat) — Tables chat_sessions et chat_messages
-- Remplace les sous-collections Firestore users/{uid}/chat_sessions et messages

create table if not exists public.chat_sessions (
    id              text        not null,
    uid             uuid        not null references public.profiles(id) on delete cascade,
    title           text,
    preview         text,
    created_at      timestamptz default now() not null,
    updated_at      timestamptz default now() not null,
    plugin_id       text,
    message_count   int         default 0 not null,
    starred         boolean     default false not null,
    deleted         boolean     default false not null,
    primary key (uid, id)
);

create index if not exists chat_sessions_uid_created on public.chat_sessions (uid, created_at desc);
alter table public.chat_sessions enable row level security;
create policy "chat_sessions_own" on public.chat_sessions
    using (auth.uid() = uid) with check (auth.uid() = uid);


create table if not exists public.chat_messages (
    id              text        not null,
    uid             uuid        not null references public.profiles(id) on delete cascade,
    session_id      text,
    text            text        not null,
    sender          text        not null,  -- 'human' | 'ai'
    type            text        default 'text',
    plugin_id       text,
    memories_id     jsonb       default '[]',
    created_at      timestamptz default now() not null,
    content_encrypted boolean   default false not null,
    deleted         boolean     default false not null,
    primary key (uid, id)
);

create index if not exists chat_messages_uid_session on public.chat_messages (uid, session_id, created_at asc);
alter table public.chat_messages enable row level security;
create policy "chat_messages_own" on public.chat_messages
    using (auth.uid() = uid) with check (auth.uid() = uid);


create table if not exists public.chat_files (
    id              text        not null,
    uid             uuid        not null references public.profiles(id) on delete cascade,
    message_id      text,
    created_at      timestamptz default now() not null,
    deleted         boolean     default false not null,
    primary key (uid, id)
);

alter table public.chat_files enable row level security;
create policy "chat_files_own" on public.chat_files
    using (auth.uid() = uid) with check (auth.uid() = uid);
