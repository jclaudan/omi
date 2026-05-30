-- Étape 21 — Table conversation_photos (remplace users/{uid}/conversations/{conv_id}/photos)
-- À exécuter après 012_goals.sql

create table if not exists public.conversation_photos (
    id              text        not null,
    uid             uuid        not null references public.profiles(id) on delete cascade,
    conversation_id text        not null,
    url             text        not null,
    metadata        jsonb       default '{}',
    created_at      timestamptz default now() not null,
    primary key (uid, id)
);

create index if not exists conversation_photos_uid_conv on public.conversation_photos (uid, conversation_id);
create index if not exists conversation_photos_created on public.conversation_photos (created_at desc);

alter table public.conversation_photos enable row level security;

create policy "conversation_photos_own"
    on public.conversation_photos for all
    using (auth.uid() = uid) with check (auth.uid() = uid);
