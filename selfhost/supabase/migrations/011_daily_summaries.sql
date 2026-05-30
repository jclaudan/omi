-- Étape 19 — Table daily_summaries (remplace users/{uid}/daily_summaries/)
-- À exécuter après 010_apps.sql

create table if not exists public.daily_summaries (
    id              text        not null,
    uid             uuid        not null references public.profiles(id) on delete cascade,
    date            date        not null,
    headline        text,
    overview        text,
    day_emoji       text,
    highlights      jsonb       default '[]',
    action_items    jsonb       default '[]',
    people_mentioned jsonb      default '[]',
    memorable_moments jsonb     default '[]',
    stats           jsonb       default '{}',
    tomorrow_focus  text,
    overall_sentiment text,
    visibility      text        default 'private',
    created_at      timestamptz default now() not null,
    updated_at      timestamptz default now() not null,
    primary key (uid, id)
);

create index if not exists daily_summaries_uid_date on public.daily_summaries (uid, date desc);
create index if not exists daily_summaries_date on public.daily_summaries (date desc);

alter table public.daily_summaries enable row level security;

create policy "daily_summaries_own"
    on public.daily_summaries for all
    using (auth.uid() = uid) with check (auth.uid() = uid);
