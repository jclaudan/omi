-- Étape 11 (v3) — Champs supplémentaires sur la table memories
-- Ajoute : user_review, reviewed, edited, kg_extracted
-- À exécuter après 002_core_schema.sql dans l'éditeur SQL Supabase.

alter table public.memories
    add column if not exists user_review  boolean,
    add column if not exists reviewed     boolean  default false not null,
    add column if not exists edited       boolean  default false not null,
    add column if not exists kg_extracted boolean  default false not null,
    add column if not exists conversation_id text;
