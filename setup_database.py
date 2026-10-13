"""Create and seed the local SQLite board-game collection database.

Games, designers, and publishers are real; users, collections, ratings, and play sessions are fictional.
"""
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "boardgames.db"

SEED = """
INSERT INTO users VALUES (1,'meeple_maven','Provo'),(2,'dice_captain','Orem'),(3,'cardboard_crafter','Salt Lake City'),(4,'tabletop_tess','Provo');
INSERT INTO publishers VALUES (1,'Stonemaier Games','United States'),(2,'Days of Wonder','France'),(3,'Czech Games Edition','Czech Republic'),(4,'Repos Production','Belgium'),(5,'Schmidt Spiele','Germany'),(6,'Z-Man Games','United States'),(7,'Starling Games','United States'),(8,'eggertspiele','Germany'),(9,'Nürnberger-Spielkarten-Verlag','Germany');
INSERT INTO designers VALUES (1,'Jamey Stegmaier'),(2,'Alan R. Moon'),(3,'Vlaada Chvátil'),(4,'Antoine Bauza'),(5,'Wolfgang Warsch'),(6,'Elizabeth Hargrave'),(7,'Matt Leacock'),(8,'Steffen Bogen'),(9,'James A. Wilson');
INSERT INTO games VALUES
(1,'Wingspan',2019,1,5,70,2.4,1),(2,'Ticket to Ride',2004,2,5,60,1.9,2),(3,'Codenames',2015,2,8,15,1.3,3),(4,'7 Wonders',2010,2,7,30,2.3,4),(5,'The Quacks of Quedlinburg',2018,2,4,45,1.9,5),(6,'Scythe',2016,1,5,115,3.4,1),(7,'Camel Up',2014,3,8,30,1.5,8),(8,'The Mind',2018,2,4,20,1.1,9),(9,'Everdell',2018,1,4,80,2.8,7),(10,'Pandemic',2008,2,4,45,2.4,6);
INSERT INTO game_designers VALUES (1,6),(2,2),(3,3),(4,4),(5,5),(6,1),(7,8),(8,5),(9,9),(10,7);
INSERT INTO genres VALUES (1,'strategy'),(2,'family'),(3,'party'),(4,'cooperative'),(5,'engine-building'),(6,'route-building'),(7,'push-your-luck');
INSERT INTO game_genres VALUES (1,1),(1,2),(1,5),(2,2),(2,6),(3,2),(3,3),(4,1),(4,2),(5,2),(5,7),(6,1),(6,5),(7,2),(7,3),(7,7),(8,2),(8,3),(8,4),(9,1),(9,5),(10,2),(10,4);
INSERT INTO collections VALUES (1,1,2020,'good'),(1,2,2018,'worn'),(1,3,2021,'good'),(1,6,2019,'good'),(1,10,2017,'worn'),(2,1,2022,'new'),(2,4,2019,'good'),(2,5,2020,'good'),(2,7,2021,'new'),(3,2,2016,'worn'),(3,3,2020,'good'),(3,8,2022,'new'),(3,9,2021,'good'),(4,1,2023,'new'),(4,4,2015,'worn'),(4,8,2020,'good'),(4,10,2018,'good');
INSERT INTO ratings VALUES (1,1,9.2,'2025-01-12'),(1,2,8.1,'2025-01-13'),(1,3,8.8,'2025-01-14'),(1,6,8.6,'2025-01-18'),(1,10,8.0,'2025-01-19'),(2,1,8.7,'2025-02-02'),(2,4,8.5,'2025-02-03'),(2,5,8.9,'2025-02-04'),(2,7,7.8,'2025-02-05'),(3,2,8.4,'2025-03-01'),(3,3,9.0,'2025-03-02'),(3,8,8.6,'2025-03-03'),(3,9,8.2,'2025-03-04'),(4,1,9.0,'2025-04-10'),(4,4,7.9,'2025-04-11'),(4,8,8.1,'2025-04-12'),(4,10,8.7,'2025-04-13');
INSERT INTO play_sessions VALUES (1,1,1,'2025-01-10',3,72,'Close game; bird combos.'),(2,1,2,'2025-01-11',4,58,'Blue route strategy won.'),(3,2,5,'2025-01-21',3,49,'Everyone pushed their luck.'),(4,2,7,'2025-01-22',5,35,'Close camel race.'),(5,3,3,'2025-02-12',6,18,'Team play.'),(6,3,8,'2025-02-13',4,23,'Reached level 9.'),(7,4,1,'2025-03-08',2,65,'Two-player session.'),(8,4,10,'2025-03-09',4,51,'Cured all four diseases.'),(9,1,6,'2025-03-15',4,124,'Long but fun.'),(10,2,1,'2025-03-16',3,75,'Tried a bird-focused strategy.');
"""

def main() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
    with sqlite3.connect(DB_PATH) as db:
        db.execute("PRAGMA foreign_keys = ON")
        db.executescript((ROOT / "schema.sql").read_text(encoding="utf-8"))
        db.executescript(SEED)
    print(f"Created {DB_PATH.name}")

if __name__ == "__main__":
    main()
