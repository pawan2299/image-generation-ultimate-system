-- [R&D CONTEXT]: Relational schema optimized for Supabase/Neon Postgres.
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE user_profiles (
    user_id BIGINT PRIMARY KEY,
    style_profile TEXT DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE asset_queue (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id BIGINT REFERENCES user_profiles(user_id),
    image_url TEXT NOT NULL,
    prompt TEXT NOT NULL,
    caption TEXT,
    posted_to_insta BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for fast Pipedream/Make.com polling
CREATE INDEX idx_unposted_assets ON asset_queue(posted_to_insta) WHERE posted_to_insta = FALSE;