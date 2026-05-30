-- Étape 5 — Initialisation utilisateur OSS+
-- À exécuter dans l'éditeur SQL de votre projet Supabase (Settings → SQL Editor).

-- 1. Table profiles (équivalent du document Firestore users/{uid})
create table if not exists public.profiles (
    id         uuid        references auth.users(id) on delete cascade primary key,
    email      text,
    created_at timestamptz default now() not null
);

-- 2. Row Level Security — chaque utilisateur ne voit que son propre profil
alter table public.profiles enable row level security;

create policy "profiles_select_own"
    on public.profiles for select
    using (auth.uid() = id);

create policy "profiles_update_own"
    on public.profiles for update
    using (auth.uid() = id);

-- 3. Trigger : crée automatiquement une ligne dans profiles lors de l'inscription
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
    insert into public.profiles (id, email)
    values (new.id, new.email)
    on conflict (id) do nothing;
    return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
    after insert on auth.users
    for each row execute function public.handle_new_user();
