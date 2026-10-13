# Prompting experiments

Model: `gpt-6-luna`. Each of the 8 questions was run once under each strategy (`python app.py --batch`, 24 runs). Every generated query was checked against a hand-written SQL query on `boardgames.db`. Raw outputs and token counts are in `runs.jsonl`.

| # | Question | Zero-shot | Single-domain | Cross-domain | Notes |
|---|---|---|---|---|---|
| 1 | Which games have the highest average rating, and what is each average? | Correct | Correct | Correct | All returned only Wingspan (8.97) and read "highest" as the single top game. |
| 2 | Which games are owned by people in Provo? | Correct | Correct | Correct | All three used `DISTINCT`; Wingspan and Pandemic are each owned by two Provo users. |
| 3 | Who designed the games with the most play sessions? | Correct | Correct | Correct | Elizabeth Hargrave (Wingspan, 3 sessions). Zero-shot returned only the designer, without the game title. |
| 4 | Which cooperative games can be played by at least four people? | Correct | **Wrong** | **Wrong** | Genres are stored lowercase. Zero-shot used `LOWER(gr.name) = 'cooperative'`; the other two used `= 'Cooperative'` and returned no rows. |
| 5 | What is the average play-session length for each game? | Correct | Correct | Correct | All used `LEFT JOIN` and reported 7 Wonders and Everdell as having no sessions. |
| 6 | Which users own Wingspan and have rated it above 9? | Correct | Correct | Correct | meeple_maven (9.2); tabletop_tess's 9.0 is correctly excluded. |
| 7 | Which publisher has the most games in users' collections? | Correct | Correct | Correct* | *Cross-domain counted copies owned (4) instead of distinct games (2). The question is ambiguous; Stonemaier wins either way. |
| 8 | What is the most popular genre based on the number of distinct games? | Correct | Correct | Correct | Family, 8 games. |

**Score:** zero-shot 8/8, single-domain 7/8, cross-domain 7/8. All 24 queries were valid SQLite, and every natural-language answer matched its returned rows.

## Worked example that succeeded

**Question:** Which users own Wingspan and have rated it above 9? (single-domain)

```sql
SELECT DISTINCT u.username
FROM users u
JOIN collections c ON c.user_id = u.user_id
JOIN games g ON g.game_id = c.game_id
JOIN ratings r ON r.user_id = u.user_id AND r.game_id = g.game_id
WHERE g.title = 'Wingspan' AND r.rating > 9
ORDER BY u.username;
```

**Rows:** `[{"username": "meeple_maven"}]`

**Answer:** meeple_maven owns Wingspan and rated it above 9.

The model joined four tables, matched the rating to the same user *and* game, and used a strict `> 9`, which correctly excludes tabletop_tess's rating of exactly 9.0.

## Worked example that failed

**Question:** Which cooperative games can be played by at least four people? (single-domain; cross-domain failed the same way)

```sql
SELECT DISTINCT g.title
FROM games g
JOIN game_genres gg ON gg.game_id = g.game_id
JOIN genres ge ON ge.genre_id = gg.genre_id
WHERE ge.name = 'Cooperative'
  AND g.max_players >= 4
ORDER BY g.title;
```

**Rows:** `[]`

**Answer:** No cooperative games for at least four people were found.

**Correct answer:** The Mind and Pandemic. Genre names are stored lowercase (`'cooperative'`), and SQLite's `=` is case-sensitive. The schema in the prompt lists column names but no sample values, so the model had to guess the capitalization. The answer step described the empty result faithfully, which makes this failure easy to miss: the answer sounds confident, and only checking the SQL shows that it's wrong.

## Compare strategies

- **Zero-shot:** Best result, 8/8. It was the only strategy to guard against case with `LOWER()`, and it used the fewest tokens.
- **Single-domain:** 7/8. The board-game examples made the output more consistent (it always used `ORDER BY` and table aliases), but they didn't help with the capitalization problem. The example `u.city='Provo'` may even have primed the model to write capitalized string literals. My own single-domain run made the same mistake (`'Strategy'`).
- **Cross-domain:** 7/8. The library example didn't cause any wrong table or column names. It shared the capitalization failure, and on question 7 it chose a different but defensible reading (copies owned rather than distinct games).
- **Conclusion:** On this small schema, all three strategies were close and the model handled joins, grouping, ties, and `LEFT JOIN`s well. The real weakness was data values the model can't see. That matches the paper's finding that including table content (sample rows) in the prompt helps. A natural next step is to add a few sample rows or the list of genre names to the schema prompt.

## Cost

The batch run used 18,194 input tokens and 4,541 output tokens across 48 API calls (two per question). The SQL-generation prompts used 2,439 input tokens for zero-shot, 3,471 for single-domain, and 3,071 for cross-domain; the examples add roughly 30–40 tokens per call. Estimated cost = `(input_tokens × input_price + output_tokens × output_price) / 1,000,000`, using the current per-million-token prices for `gpt-6-luna`.

## My own question

I asked for highly rated "Euro-style" games that support 4 or more players (`max_players >= 4`), then rephrased the question twice. The database has no "Euro" genre; the closest stored genre is `strategy`. Every strategy game supports at least 4 players, so the correct answer is Wingspan (8.97), Scythe (8.6), 7 Wonders (8.2), and Everdell (8.2).

| Question | Strategy | Result |
|---|---|---|
| What are the top-rated Euro-style games that play 4 players or more? | Zero-shot | Wrong: genre `LIKE '%Euro%'` matched nothing, so no rows |
| What are the best reated strategy games the can play 4 or more players? | Single-domain | **Wrong:** `ge.name = 'Strategy'` (capitalized), so no rows |
| What are the strategy games that can play 4 or more players? | Cross-domain | **Correct:** 7 Wonders, Everdell, Scythe, Wingspan |

All three runs read "4 or more players" as `max_players >= 4`, as I intended. The typos in the second question ("reated", "the can") didn't confuse the model.

### Run 1: "Euro-style" (zero-shot)

```sql
SELECT g.title, AVG(r.rating) AS average_rating
FROM games AS g
JOIN ratings AS r ON r.game_id = g.game_id
WHERE g.max_players >= 4
  AND EXISTS (
    SELECT 1
    FROM game_genres AS gg
    JOIN genres AS ge ON ge.genre_id = gg.genre_id
    WHERE gg.game_id = g.game_id
      AND ge.name LIKE '%Euro%'
  )
GROUP BY g.game_id, g.title
ORDER BY average_rating DESC;
```

**Rows:** `[]`

**Answer:** No games were found that match those criteria.

The model searched for a genre literally named like "Euro" instead of mapping the term onto a stored genre. The prompt tells it to use only what's in the database, and it can't see genre values, so it guessed. Returning nothing is defensible, but not useful.

### Run 2: "best reated strategy games" (single-domain)

```sql
SELECT g.title, ROUND(AVG(r.rating), 2) AS avg_rating
FROM games g
JOIN game_genres gg ON gg.game_id = g.game_id
JOIN genres ge ON ge.genre_id = gg.genre_id
JOIN ratings r ON r.game_id = g.game_id
WHERE ge.name = 'Strategy'
  AND g.max_players >= 4
GROUP BY g.game_id, g.title
ORDER BY avg_rating DESC;
```

**Rows:** `[]`

**Answer:** No strategy games for 4 or more players were found in the results.

The query is correct except for one character: genres are stored lowercase. It's the same failure as batch question 4, and again in single-domain mode.

### Run 3: "strategy games" (cross-domain)

```sql
SELECT DISTINCT g.title
FROM games g
JOIN game_genres gg ON gg.game_id = g.game_id
JOIN genres gen ON gen.genre_id = gg.genre_id
WHERE gen.name = 'strategy'
  AND g.max_players >= 4
ORDER BY g.title;
```

**Answer:** The strategy games that can play 4 or more players are **7 Wonders, Everdell, Scythe, and Wingspan**.

Correct. This version of the question didn't ask about ratings, so the results aren't ranked.

### Takeaway

Two of my three runs returned an empty result. Both times, the natural-language answer confidently said nothing matched. The SQL structure (joins, grouping, player filter) was right every time; the failures came from string values the model couldn't see. Giving the model the stored genre names in the prompt would likely fix both.
