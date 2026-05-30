-- Étape 15 (users) — Extension de la table profiles
-- Ajoute toutes les colonnes du document Firestore users/{uid}
-- À exécuter après 007_conversation_photos.sql

alter table public.profiles
    add column if not exists name                     text,
    add column if not exists email                    text,
    add column if not exists language                 text      default 'en',
    add column if not exists store_recording_permission boolean  default false not null,
    add column if not exists private_cloud_sync_enabled boolean  default true  not null,
    add column if not exists data_protection_level    text      default 'standard',
    -- Subscription (storé en JSONB pour flexibilité)
    add column if not exists subscription             jsonb     default '{}'  not null,
    add column if not exists stripe_customer_id       text,
    -- BYOK — fingerprints uniquement (jamais les clés)
    add column if not exists byok                     jsonb     default '{}'  not null,
    -- Préférences
    add column if not exists transcription_prefs      jsonb     default '{}'  not null,
    add column if not exists notification_settings    jsonb     default '{}'  not null,
    add column if not exists assistant_settings       jsonb     default '{}'  not null,
    add column if not exists ai_profile               jsonb     default '{}'  not null,
    -- Speaker embedding de l'utilisateur lui-même
    add column if not exists speaker_embedding        jsonb,
    -- Champ fourre-tout pour les champs non-typés
    add column if not exists metadata                 jsonb     default '{}'  not null;

-- Table intégrations (remplace sous-collection users/{uid}/integrations/{app_key})
create table if not exists public.user_integrations (
    uid      uuid  not null references public.profiles(id) on delete cascade,
    app_key  text  not null,
    data     jsonb not null default '{}',
    primary key (uid, app_key)
);

alter table public.user_integrations enable row level security;
create policy "user_integrations_own" on public.user_integrations
    using (auth.uid() = uid) with check (auth.uid() = uid);

-- Table intégrations de tâches (remplace sous-collection users/{uid}/task_integrations/{app_key})
create table if not exists public.user_task_integrations (
    uid      uuid  not null references public.profiles(id) on delete cascade,
    app_key  text  not null,
    data     jsonb not null default '{}',
    primary key (uid, app_key)
);

alter table public.user_task_integrations enable row level security;
create policy "user_task_integrations_own" on public.user_task_integrations
    using (auth.uid() = uid) with check (auth.uid() = uid);
