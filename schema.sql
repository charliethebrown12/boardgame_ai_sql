PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT NOT NULL UNIQUE, city TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS publishers (publisher_id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, country TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS designers (designer_id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE);
CREATE TABLE IF NOT EXISTS games (
  game_id INTEGER PRIMARY KEY, title TEXT NOT NULL, year_published INTEGER NOT NULL,
  min_players INTEGER NOT NULL, max_players INTEGER NOT NULL, play_time_minutes INTEGER NOT NULL,
  complexity REAL NOT NULL, publisher_id INTEGER NOT NULL REFERENCES publishers(publisher_id)
);
CREATE TABLE IF NOT EXISTS game_designers (
  game_id INTEGER NOT NULL REFERENCES games(game_id), designer_id INTEGER NOT NULL REFERENCES designers(designer_id),
  PRIMARY KEY (game_id, designer_id)
);
CREATE TABLE IF NOT EXISTS genres (genre_id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE);
CREATE TABLE IF NOT EXISTS game_genres (
  game_id INTEGER NOT NULL REFERENCES games(game_id), genre_id INTEGER NOT NULL REFERENCES genres(genre_id),
  PRIMARY KEY (game_id, genre_id)
);
CREATE TABLE IF NOT EXISTS collections (
  user_id INTEGER NOT NULL REFERENCES users(user_id), game_id INTEGER NOT NULL REFERENCES games(game_id),
  owned_since INTEGER NOT NULL, condition TEXT NOT NULL CHECK (condition IN ('new', 'good', 'worn')),
  PRIMARY KEY (user_id, game_id)
);
CREATE TABLE IF NOT EXISTS ratings (
  user_id INTEGER NOT NULL REFERENCES users(user_id), game_id INTEGER NOT NULL REFERENCES games(game_id),
  rating REAL NOT NULL CHECK (rating BETWEEN 1 AND 10), rated_on TEXT NOT NULL,
  PRIMARY KEY (user_id, game_id)
);
CREATE TABLE IF NOT EXISTS play_sessions (
  session_id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(user_id),
  game_id INTEGER NOT NULL REFERENCES games(game_id), played_on TEXT NOT NULL,
  player_count INTEGER NOT NULL, duration_minutes INTEGER NOT NULL, notes TEXT
);
