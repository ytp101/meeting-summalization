-- 1) Table
CREATE TABLE IF NOT EXISTS meeting_summary (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    work_id       TEXT NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    source_filename   TEXT,
    source_path       TEXT,
    wav_path          TEXT,
    transcript_path   TEXT,
    summary_path      TEXT
);

-- Optional: quick lookup by work_id
CREATE INDEX IF NOT EXISTS idx_meeting_summary_work_id ON meeting_summary (work_id);

-- 2) Trigger function to auto-update `updated_at`
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 3) Trigger: before any UPDATE, refresh `updated_at`
DROP TRIGGER IF EXISTS trg_set_updated_at ON meeting_summary;
CREATE TRIGGER trg_set_updated_at
BEFORE UPDATE ON meeting_summary
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();
