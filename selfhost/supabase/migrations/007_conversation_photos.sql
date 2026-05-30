-- Étape 13 (v5) — Table conversation_photos (sub-collection Firestore → table Supabase)
-- Stocke les photos associées à une conversation (base64 chiffrée optionnelle côté app)

create table if not exists public.conversation_photos (
    id             text        not null,
    uid            uuid        not null references public.profiles(id) on delete cascade,
    conversation_id text       not null,
    base64          text,
    description     text,
    created_at      timestamptz default now() not null,
    primary key (uid, id)
);

create index if not exists conversation_photos_uid_conversation
    on public.conversation_photos (uid, conversation_id);

alter table public.conversation_photos enable row level security;

create policy "conversation_photos_select_own"
    on public.conversation_photos for select using (auth.uid() = uid);
create policy "conversation_photos_insert_own"
    on public.conversation_photos for insert with check (auth.uid() = uid);
create policy "conversation_photos_update_own"
    on public.conversation_photos for update using (auth.uid() = uid);
create policy "conversation_photos_delete_own"
    on public.conversation_photos for delete using (auth.uid() = uid);

-- Ajoute is_locked sur memories (manquant du schéma initial)
alter table public.memories
    add column if not exists is_locked boolean default false not null;
