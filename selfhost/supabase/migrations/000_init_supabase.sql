-- Initialize Supabase schemas and extensions
-- Must run before other migrations

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create auth schema
CREATE SCHEMA IF NOT EXISTS auth;

-- Create minimal auth.users table structure for OSS+ compatibility
CREATE TABLE IF NOT EXISTS auth.users (
    id uuid PRIMARY KEY,
    email text NOT NULL UNIQUE,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

-- Create public schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS public;

-- Create storage schema for Supabase compatibility
CREATE SCHEMA IF NOT EXISTS storage;

-- Create database roles
CREATE ROLE anon NOLOGIN;
CREATE ROLE authenticated NOLOGIN;
CREATE ROLE service_role SUPERUSER NOLOGIN;

-- Grant permissions
GRANT USAGE ON SCHEMA auth TO anon;
GRANT USAGE ON SCHEMA auth TO authenticated;
GRANT USAGE ON SCHEMA public TO anon;
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT ALL PRIVILEGES ON SCHEMA auth TO service_role;
GRANT ALL PRIVILEGES ON SCHEMA public TO service_role;

-- Allow postgrest to connect
ALTER ROLE anon WITH NOLOGIN;
ALTER ROLE authenticated WITH NOLOGIN;
ALTER ROLE service_role WITH SUPERUSER;

-- Create auth helper functions (normally provided by GoTrue)
CREATE OR REPLACE FUNCTION auth.uid() RETURNS uuid AS $$
  SELECT COALESCE(
    current_setting('request.jwt.claims', true)::jsonb->>'sub',
    current_setting('request.jwt.claim.sub', true)
  )::uuid;
$$ LANGUAGE SQL STABLE;

-- Create current_user_id function (commonly used helper)
CREATE OR REPLACE FUNCTION public.current_user_id() RETURNS uuid AS $$
  SELECT auth.uid();
$$ LANGUAGE SQL STABLE;
