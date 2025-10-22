import json
from PlayerClub_Data.models import Club, Player

with open("PlayerClub_Data/data/club_stats.json", "r", encoding="utf-8") as f:
    clubs = json.load(f)

for c in clubs:
    club, created = Club.objects.update_or_create(
        name=c["team"],
        season=c["season"],
        league=c["league"],
        defaults={
            "total_goal": c.get("gls", 0),
            "total_assist": c.get("ast", 0),
            "expected_xg": c.get("xg", 0.0),
            "expected_xag": c.get("xag", 0.0),
        }
    )
    print(f"{'Created' if created else ' Updated'} Club: {club.name}")

#Import Data Player
with open("PlayerClub_Data/data/player_stats.json", "r", encoding="utf-8") as f:
    players = json.load(f)

for p in players:
    club = Club.objects.filter(
        name=p["team"],
        league=p["league"],
        season=p["season"]
    ).first()

    if not club:
        print(f"Club not found for {p['player']} ({p['team']})")
        continue

    player, created = Player.objects.update_or_create(
        name=p["player"],
        club=club,
        defaults={
            "nation": p.get("nation"),
            "position": p.get("position"),
            "age": p.get("age"),
            "born": p.get("born"),
            "goals": p.get("goals", 0),
            "assists": p.get("assists", 0),
            "xg": p.get("xg", 0),
            "npxg": p.get("npxg", 0),
            "xag": p.get("xag", 0),
            "Progressive_Carries": p.get("prgc", 0),
            "Progressive_Passes": p.get("prgp", 0),
            "Progressive_Receptions": p.get("prgr", 0),
            "passes_completed": p.get("passes_completed", 0),
            "passes_attempted": p.get("passes_attempted", 0),
            "pass_accuracy": p.get("pass_accuracy", 0),
            "tackles": p.get("tackles", 0),
            "tackles_won": p.get("tackles_won", 0),
            "challenges_won": p.get("challenges_won", 0),
            "challenges_attempted": p.get("challenges_attempted", 0),
            "blocks": p.get("blocks", 0),
            "clearances": p.get("clearances", 0),
            "saves": p.get("saves"),
            "save_percentage": p.get("save_percentage"),
            "clean_sheets": p.get("clean_sheets"),
            "clean_sheet_percentage": p.get("clean_sheet_percentage"),
        }
    )
    print(f"{'🆕 Created' if created else 'Updated'} Player: {player.name} ({club.name})")


