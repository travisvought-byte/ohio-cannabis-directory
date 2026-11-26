-- Silver Cup: who entered, their runs, and every run sent in with what the replay made of it.
CREATE TABLE IF NOT EXISTS entrants (
  hkey TEXT PRIMARY KEY,          -- the captain name, folded for matching
  handle TEXT NOT NULL,           -- the captain name as shown on the board
  email TEXT NOT NULL,            -- never shown: only for reaching a winner
  crew TEXT NOT NULL DEFAULT '',  -- optional crew or business, for the crews board
  ckey TEXT NOT NULL DEFAULT '',
  created INTEGER NOT NULL,
  dq TEXT NOT NULL DEFAULT ''     -- set when a captain is disqualified, with the reason
);
CREATE TABLE IF NOT EXISTS runs (
  id TEXT PRIMARY KEY,
  hkey TEXT NOT NULL,
  seed INTEGER NOT NULL,
  tok TEXT NOT NULL,              -- a hash of the run's key, never the key itself
  practice INTEGER NOT NULL,
  ver TEXT NOT NULL,
  started INTEGER NOT NULL,
  last_sub INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS runs_hkey ON runs(hkey);
CREATE TABLE IF NOT EXISTS subs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run TEXT NOT NULL,
  at INTEGER NOT NULL,
  steps INTEGER NOT NULL,
  size INTEGER NOT NULL,
  body BLOB,                      -- the recorded moves, gzipped; cleared once a later send of the same run is checked
  claim INTEGER NOT NULL DEFAULT 0,
  over TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'pending',   -- pending, ok, refused, error (the checker's own fault), superseded
  xp INTEGER NOT NULL DEFAULT 0,
  level INTEGER NOT NULL DEFAULT 0,
  day INTEGER NOT NULL DEFAULT 0,
  stats TEXT NOT NULL DEFAULT '{}',
  reason TEXT NOT NULL DEFAULT '',
  checked INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS subs_status ON subs(status, id);
CREATE INDEX IF NOT EXISTS subs_run ON subs(run, id);
CREATE TABLE IF NOT EXISTS limits (
  k TEXT PRIMARY KEY,
  n INTEGER NOT NULL,
  until INTEGER NOT NULL
);
