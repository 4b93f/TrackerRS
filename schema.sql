CREATE TABLE IF NOT EXISTS users (
    platform TEXT NOT NULL,
    user_id TEXT NOT NULL,
    username TEXT NOT NULL,
    token TEXT NOT NULL,
    last_media_id TEXT,
    refresh_token TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (platform, user_id)
);
