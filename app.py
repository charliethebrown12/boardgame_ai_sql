"""Ask natural-language questions about the sample board-game database."""
from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "boardgames.db"
LOG_PATH = ROOT / "runs.jsonl"
MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")
SCHEMA = """
users(user_id PK, username, city)
publishers(publisher_id PK, name, country)
designers(designer_id PK, name)
games(game_id PK, title, year_published, min_players, max_players, play_time_minutes, complexity, publisher_id FK -> publishers.publisher_id)
game_designers(game_id FK -> games.game_id, designer_id FK -> designers.designer_id)
genres(genre_id PK, name)
game_genres(game_id FK -> games.game_id, genre_id FK -> genres.genre_id)
collections(user_id FK -> users.user_id, game_id FK -> games.game_id, owned_since, condition)
ratings(user_id FK -> users.user_id, game_id FK -> games.game_id, rating, rated_on)
play_sessions(session_id PK, user_id FK -> users.user_id, game_id FK -> games.game_id, played_on, player_count, duration_minutes, notes)
""".strip()

EXAMPLES = {
    "single_domain": """
Worked examples from this same board-game database:
Q: Which games have an average rating above 8.5?
SQL: SELECT g.title, ROUND(AVG(r.rating), 2) AS avg_rating FROM games g JOIN ratings r ON r.game_id=g.game_id GROUP BY g.game_id,g.title HAVING AVG(r.rating)>8.5 ORDER BY avg_rating DESC;
Q: Which games are owned by users in Provo?
SQL: SELECT DISTINCT g.title FROM games g JOIN collections c ON c.game_id=g.game_id JOIN users u ON u.user_id=c.user_id WHERE u.city='Provo' ORDER BY g.title;
""".strip(),
    "cross_domain": """
Worked example from another domain (a library database):
Q: Which authors have at least two books?
SQL: SELECT a.name,COUNT(*) AS book_count FROM authors a JOIN books b ON b.author_id=a.author_id GROUP BY a.author_id,a.name HAVING COUNT(*)>=2 ORDER BY book_count DESC;
Learn only the SQL pattern; use only names from the current board-game schema.
""".strip(),
}

def sql_instructions(strategy: str) -> str:
    prompt = f"""Translate the user's question into exactly one SQLite query. Use only the schema and facts in this database; do not use outside knowledge. Return SQL only, without markdown. The query must be read-only: use SELECT (WITH is allowed only when it ends in SELECT). Never use INSERT, UPDATE, DELETE, DDL, PRAGMA, ATTACH, or multiple statements. If it cannot be answered from the schema, return SELECT 'Not answerable from this database' AS message;.

Schema:
{SCHEMA}
"""
    if strategy in EXAMPLES:
        prompt += "\n" + EXAMPLES[strategy]
    return prompt

def get_sql(client: OpenAI, question: str, strategy: str) -> tuple[str, dict]:
    response = client.responses.create(model=MODEL, instructions=sql_instructions(strategy), input=question)
    sql = re.sub(r"^```(?:sql)?\s*|\s*```$", "", response.output_text.strip(), flags=re.I).strip()
    usage = getattr(response, "usage", None)
    return sql, {"input_tokens": getattr(usage, "input_tokens", None), "output_tokens": getattr(usage, "output_tokens", None)}

def query_read_only(sql: str) -> list[dict]:
    if not DB_PATH.exists():
        raise RuntimeError("Database missing. Run: python setup_database.py")
    db = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA query_only = ON")
    allowed = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION}
    if hasattr(sqlite3, "SQLITE_RECURSIVE"):
        allowed.add(sqlite3.SQLITE_RECURSIVE)
    db.set_authorizer(lambda action, *_: sqlite3.SQLITE_OK if action in allowed else sqlite3.SQLITE_DENY)
    try:
        return [dict(row) for row in db.execute(sql).fetchmany(100)]
    finally:
        db.close()

def explain(client: OpenAI, question: str, sql: str, rows: list[dict]) -> tuple[str, dict]:
    response = client.responses.create(
        model=MODEL,
        instructions=("Answer in plain language using only the supplied SQL result. Do not add facts from general knowledge. If no rows were found, say so. If 100 rows are shown, mention that output may be truncated."),
        input=json.dumps({"question": question, "sql": sql, "schema": SCHEMA, "rows": rows}, ensure_ascii=False),
    )
    usage = getattr(response, "usage", None)
    return response.output_text.strip(), {"input_tokens": getattr(usage, "input_tokens", None), "output_tokens": getattr(usage, "output_tokens", None)}

STRATEGIES = ("zero_shot", *EXAMPLES)

BATCH_QUESTIONS = [
    "Which games have the highest average rating, and what is each average?",
    "Which games are owned by people in Provo?",
    "Who designed the games with the most play sessions?",
    "Which cooperative games can be played by at least four people?",
    "What is the average play-session length for each game?",
    "Which users own Wingspan and have rated it above 9?",
    "Which publisher has the most games in users' collections?",
    "What is the most popular genre based on the number of distinct games?",
]

def run_question(client: OpenAI, question: str, strategy: str) -> dict:
    sql, sql_usage = get_sql(client, question, strategy)
    print(f"\n[{strategy}] {question}\nGenerated SQL:\n{sql}")
    record = {"timestamp_utc": datetime.now(timezone.utc).isoformat(), "model": MODEL,
              "strategy": strategy, "question": question, "sql": sql, "tokens": {"sql_call": sql_usage}}
    try:
        rows = query_read_only(sql)
    except sqlite3.Error as error:
        print(f"SQLite rejected the query: {error}")
        record["error"] = str(error)
    else:
        answer, answer_usage = explain(client, question, sql, rows)
        print(f"Answer: {answer}")
        record.update(rows=rows, answer=answer)
        record["tokens"]["answer_call"] = answer_usage
    with LOG_PATH.open("a", encoding="utf-8") as out:
        out.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record

def main() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("Set OPENAI_API_KEY in your shell before running the app.")
    from openai import APIError, OpenAI
    try:
        run_app(OpenAI())
    except APIError as error:
        raise SystemExit(f"OpenAI API error: {error}")

def run_app(client: OpenAI) -> None:
    if "--batch" in sys.argv:
        for question in BATCH_QUESTIONS:
            for strategy in STRATEGIES:
                run_question(client, question, strategy)
        print(f"\nSaved {len(BATCH_QUESTIONS) * len(STRATEGIES)} runs to {LOG_PATH.name}")
        return
    question = input("Ask about the board-game database: ").strip()
    strategy = input("Strategy [zero_shot/single_domain/cross_domain] (zero_shot): ").strip() or "zero_shot"
    if strategy not in STRATEGIES:
        raise SystemExit("Choose zero_shot, single_domain, or cross_domain.")
    if not question:
        raise SystemExit("Please enter a question.")
    run_question(client, question, strategy)
    print(f"\nSaved this run to {LOG_PATH.name}")

if __name__ == "__main__":
    main()
