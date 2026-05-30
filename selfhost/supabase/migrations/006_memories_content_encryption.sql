-- Étape 12 (v4) — Chiffrement du contenu des memories
-- Ajoute content_encrypted (flag) sur la table memories
-- À exécuter après 005_conversations_extra_cols.sql

alter table public.memories
    add column if not exists content_encrypted boolean default false not null;
