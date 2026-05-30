-- Étape 17 — Table apps (remplace la collection Firestore plugins_data/)
-- Supporte les apps publiques (uid NULL) et privées (uid = créateur).
-- En mode self-hosted, approved = true par défaut (pas de processus de review).
-- À exécuter après 009_chat.sql

create table if not exists public.apps (
    id              text        not null primary key,
    uid             uuid        references public.profiles(id) on delete set null,
    name            text        not null,
    description     text,
    author          text,
    category        text        default 'other',
    image           text,
    -- capabilities : ['memories', 'chat', 'external_integration', 'persona', …]
    capabilities    jsonb       not null default '[]',
    private         boolean     not null default false,
    approved        boolean     not null default true,   -- true par défaut en self-hosted
    status          text        default 'approved',
    disabled        boolean     not null default false,
    -- Intégration externe (webhook_url, triggers_on, etc.)
    external_integration jsonb,
    -- Prompts LLM (apps de type prompt)
    memory_prompt   text,
    chat_prompt     text,
    persona_prompt  text,
    -- Statistiques légères
    installs        int         default 0 not null,
    rating_avg      float       default 0,
    rating_count    int         default 0 not null,
    is_popular      boolean     default false not null,
    -- Champs divers (prix, tags, thumbnails…)
    metadata        jsonb       not null default '{}',
    created_at      timestamptz default now() not null,
    updated_at      timestamptz default now() not null,
    deleted         boolean     default false not null
);

create index if not exists apps_uid         on public.apps (uid);
create index if not exists apps_category    on public.apps (category);
create index if not exists apps_approved    on public.apps (approved, private, deleted);

alter table public.apps enable row level security;

-- Tout le monde peut lire les apps publiques (approved + non-private)
create policy "apps_select_public"
    on public.apps for select
    using (
        (approved = true and private = false and deleted = false)
        or (uid = auth.uid())
    );

-- Seul le créateur peut gérer ses apps privées ; admin via service_role
create policy "apps_insert_own"
    on public.apps for insert
    with check (uid = auth.uid());

create policy "apps_update_own"
    on public.apps for update
    using (uid = auth.uid());

create policy "apps_delete_own"
    on public.apps for delete
    using (uid = auth.uid());

-- Table des apps activées par utilisateur
-- Remplace le champ enabled_app_ids dans le profil Firestore
create table if not exists public.user_enabled_apps (
    uid     uuid not null references public.profiles(id) on delete cascade,
    app_id  text not null references public.apps(id) on delete cascade,
    primary key (uid, app_id)
);

alter table public.user_enabled_apps enable row level security;

create policy "user_enabled_apps_own"
    on public.user_enabled_apps for all
    using (auth.uid() = uid) with check (auth.uid() = uid);
