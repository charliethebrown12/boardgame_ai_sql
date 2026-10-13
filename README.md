# Board Game Collection: AI + SQL

This project models a fictional board-game community built around real games. It stores a game catalog, publishers, designers, genres, user collections, ratings, and play sessions. A command-line app translates plain English into SQLite, runs the query, and asks the model to explain the returned rows.

## Files

- `app.py` — two-call natural-language SQL app and three prompt strategies.
- `schema.sql` — relational schema and foreign keys.
- `setup_database.py` — creates and seeds `boardgames.db` with fictional sample data.
- `boardgames.db` — the seeded SQLite database (regenerate with `setup_database.py`).
- `schema.png` / `schema.svg` — schema picture.
- `examples.md` — experiment results: eight test questions under three strategies, plus my own question.
- `runs.jsonl` — raw log of every run (question, SQL, rows, answer, token counts).
- `.env.example` — variable names only; never put a real API key in a shared file.

## Run it

1. Install Python 3.10 or later.
2. Create and activate a virtual environment; run `pip install -r requirements.txt`.
3. Run `python setup_database.py`.
4. Create your own OpenAI API key and set it as the `OPENAI_API_KEY` environment variable. In Windows PowerShell use `$env:OPENAI_API_KEY="your-key"`; in macOS/Linux use `export OPENAI_API_KEY="your-key"`. Do not paste the key into this chat or commit it. Optionally set `OPENAI_MODEL` to a model available to your account.
5. Run `python app.py`, enter a question, then choose `zero_shot`, `single_domain`, or `cross_domain`.
6. To run all eight questions from `examples.md` under all three strategies (48 API calls), run `python app.py --batch`.

Each question uses two API calls: generate SQL, then explain query results. The app prints the SQL and appends it with result rows and token counts to `runs.jsonl`. The committed `runs.jsonl` holds the runs reported in `examples.md`. Check the current model availability and API prices before running. To estimate cost, multiply input and output tokens by the current per-token rates; prices and model names can change.

## Design notes

`game_designers` and `game_genres` are bridge tables for many-to-many relationships. `collections`, `ratings`, and `play_sessions` represent distinct user-game relationships. The games, designers, and publishers are real; users, collections, ratings, and play sessions are fictional.

## Prompting experiment

The three modes reflect the zero-shot, single-domain, and cross-domain settings examined by Chang and Fosler-Lussier (2023). Zero-shot sends the schema only; single-domain includes two board-game examples; cross-domain includes an example from a different schema. Run the same questions in each mode. Compare SQL validity, returned rows, and whether the natural-language response describes those rows accurately. Record actual runs in `examples.md`.

## Limits

The database opens read-only, SQLite query-only mode is on, and an authorizer permits only reads. This is a class demo, not a production security boundary. The model can produce invalid or semantically wrong SQL, and the answer step can misread results. Inspect the generated SQL and compare it with direct SQL queries.

## Paper

Chang, Shuaichen, and Eric Fosler-Lussier. “How to Prompt LLMs for Text-to-SQL: A Study in Zero-shot, Single-domain, and Cross-domain Settings.” arXiv:2305.11853 (2023). https://arxiv.org/abs/2305.11853
