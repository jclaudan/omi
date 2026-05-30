-- Étape 22 — Table phone_numbers (remplace users/{uid}/phone_numbers)
-- À exécuter après 013_photos.sql

create table if not exists public.phone_numbers (
    id                  text        not null,
    uid                 uuid        not null references public.profiles(id) on delete cascade,
    phone_number        text,
    phone_number_hash   text,
    verified            boolean     default false not null,
    data_protection_level text      default 'standard',
    created_at          timestamptz default now() not null,
    updated_at          timestamptz default now() not null,
    primary key (uid, id)
);

create index if not exists phone_numbers_uid on public.phone_numbers (uid);
create index if not exists phone_numbers_hash on public.phone_numbers (phone_number_hash);

alter table public.phone_numbers enable row level security;

create policy "phone_numbers_own"
    on public.phone_numbers for all
    using (auth.uid() = uid) with check (auth.uid() = uid);
