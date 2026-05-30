-- Étape 12 (v4) — Colonnes supplémentaires sur la table conversations
-- Ajoute : visibility, starred (manquants du schéma initial)
-- À exécuter après 004_conversations_encryption.sql

alter table public.conversations
    add column if not exists visibility text    default 'shared',
    add column if not exists starred    boolean default false not null,
    add column if not exists is_locked  boolean default false not null;
