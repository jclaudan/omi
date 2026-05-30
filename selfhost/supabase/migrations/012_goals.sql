-- Étape 20 — Tables goals + goal_history
-- À exécuter après 011_daily_summaries.sql

create table if not exists public.goals (
    id              text        not null,
    uid             uuid        not null references public.profiles(id) on delete cascade,
    title           text        not null,
    description     text,
    category        text,
    target_value    float,
    current_value   float       default 0,
    unit            text,
    is_active       boolean     default true not null,
    created_at      timestamptz default now() not null,
    updated_at      timestamptz default now() not null,
    ended_at        timestamptz,
    metadata        jsonb       default '{}',
    primary key (uid, id)
);

create table if not exists public.goal_history (
    id              text        not null,
    uid             uuid        not null references public.profiles(id) on delete cascade,
    goal_id         text        not null,
    date            date        not null,
    value           float       not null,
    recorded_at     timestamptz default now() not null,
    primary key (uid, goal_id, date)
);

create index if not exists goals_uid_active on public.goals (uid, is_active);
create index if not exists goals_uid_created on public.goals (uid, created_at desc);
create index if not exists goal_history_goal_date on public.goal_history (goal_id, date desc);
create index if not exists goal_history_uid_date on public.goal_history (uid, date desc);

alter table public.goals enable row level security;
alter table public.goal_history enable row level security;

create policy "goals_own"
    on public.goals for all
    using (auth.uid() = uid) with check (auth.uid() = uid);

create policy "goal_history_own"
    on public.goal_history for all
    using (auth.uid() = uid) with check (auth.uid() = uid);
