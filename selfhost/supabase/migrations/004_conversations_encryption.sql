-- Étape 11 (v3) — Chiffrement côté application pour les segments dans Postgres
-- Ajoute un flag pour indiquer que transcript_segments est chiffré côté app
-- À exécuter après 003_memories_extra_fields.sql dans l'éditeur SQL Supabase.

alter table public.conversations
    add column if not exists transcript_segments_encrypted boolean default false not null;
