"""
Premier League Stats Scraper
Data source: Sofascore unofficial API
"""
import requests
import time

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Referer": "https://www.sofascore.com/",
}

BASE          = "https://api.sofascore.com/api/v1"
TOURNAMENT_ID = 17  # Premier League

SEASONS = {
    "25/26": 76986,
    "24/25": 61627,
    "23/24": 52186,
}
DEFAULT_SEASON = "25/26"


def _get(path: str, params: dict | None = None) -> dict:
    time.sleep(0.3)
    resp = requests.get(BASE + path, headers=HEADERS, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def get_season_id(season: str = DEFAULT_SEASON) -> int:
    return SEASONS.get(season, SEASONS[DEFAULT_SEASON])


# ── Standings ──────────────────────────────────────────────────────────────

def get_standings(season: str = DEFAULT_SEASON) -> list[dict]:
    sid  = get_season_id(season)
    data = _get(f"/unique-tournament/{TOURNAMENT_ID}/season/{sid}/standings/total")
    rows = data.get("standings", [{}])[0].get("rows", [])
    result = []
    for r in rows:
        team   = r.get("team", {})
        colors = team.get("teamColors", {})
        result.append({
            "position":  r.get("position"),
            "team":      team.get("name"),
            "team_id":   team.get("id"),
            "team_code": team.get("nameCode"),
            "team_color": colors.get("primary", "#38003c"),
            "promotion": r.get("promotion", {}).get("text", ""),
            "played":    r.get("matches"),
            "wins":      r.get("wins"),
            "draws":     r.get("draws"),
            "losses":    r.get("losses"),
            "gf":        r.get("scoresFor"),
            "ga":        r.get("scoresAgainst"),
            "gd":        r.get("scoreDiffFormatted"),
            "points":    r.get("points"),
        })
    return result


# ── Team Stats ─────────────────────────────────────────────────────────────

def get_team_stats(season: str = DEFAULT_SEASON) -> list[dict]:
    standings = get_standings(season)
    sid = get_season_id(season)
    result = []
    for row in standings:
        tid = row["team_id"]
        try:
            data = _get(f"/team/{tid}/unique-tournament/{TOURNAMENT_ID}/season/{sid}/statistics/overall")
            s = data.get("statistics", {})

            def pct(num, den):
                return round(num / den * 100, 1) if den else None

            result.append({
                "position":          row["position"],
                "team":              row["team"],
                "played":            row["played"],
                # Attack
                "goals":             s.get("goalsScored"),
                "conceded":          s.get("goalsConceded"),
                "assists":           s.get("assists"),
                "shots":             s.get("shots"),
                "shots_on_target":   s.get("shotsOnTarget"),
                "shot_acc_%":        pct(s.get("shotsOnTarget", 0), s.get("shots", 0)),
                "big_chances":       s.get("bigChances"),
                "big_chances_created": s.get("bigChancesCreated"),
                "big_chances_missed":  s.get("bigChancesMissed"),
                "hit_woodwork":      s.get("hitWoodwork"),
                "fast_break_goals":  s.get("fastBreakGoals"),
                "headed_goals":      s.get("headedGoals"),
                "penalty_goals":     s.get("penaltyGoals"),
                # Possession / Passing
                "possession_%":      round(s.get("averageBallPossession", 0), 1),
                "pass_acc_%":        round(s.get("accuratePassesPercentage", 0), 1),
                "long_ball_acc_%":   round(s.get("accurateLongBallsPercentage", 0), 1),
                "cross_acc_%":       round(s.get("accurateCrossesPercentage", 0), 1),
                # Defense
                "tackles":           s.get("tackles"),
                "interceptions":     s.get("interceptions"),
                "clearances":        s.get("clearances"),
                "aerial_won_%":      round(s.get("aerialDuelsWonPercentage", 0), 1),
                "duel_won_%":        round(s.get("duelsWonPercentage", 0), 1),
                "errors_goal":       s.get("errorsLeadingToGoal"),
                "clean_sheets":      s.get("cleanSheets"),
                "saves":             s.get("saves"),
                # Big chances against
                "big_chances_against": s.get("bigChancesAgainst"),
                # Discipline
                "yellow_cards":      s.get("yellowCards"),
                "red_cards":         s.get("redCards"),
                "fouls":             s.get("fouls"),
                "offsides":          s.get("offsides"),
            })
        except Exception:
            result.append({"position": row["position"], "team": row["team"]})
    return result


# ── Player Stat Definitions ────────────────────────────────────────────────

STAT_FIELDS = {
    # Standard
    "standard": (
        "goals,assists,yellowCards,redCards,rating,minutesPlayed,appearances",
        "-goals",
    ),
    # xG / Expected
    "expected": (
        "expectedGoals,expectedAssists,expectedGoalsOnTarget,"
        "goals,assists,bigChancesCreated,bigChancesMissed,"
        "totalShots,shotsOnTarget,minutesPlayed,appearances",
        "-expectedGoals",
    ),
    # Shooting
    "shooting": (
        "goals,totalShots,shotsOnTarget,shotsOffTarget,"
        "goalConversionPercentage,bigChancesCreated,bigChancesMissed,"
        "hitWoodwork,penaltyGoals,leftFootGoals,rightFootGoals,headedGoals,"
        "minutesPlayed,appearances",
        "-goals",
    ),
    # Passing / Creation
    "passing": (
        "assists,expectedAssists,keyPasses,accuratePasses,inaccuratePasses,"
        "accurateLongBalls,accurateCrosses,bigChancesCreated,"
        "successfulDribbles,minutesPlayed,appearances",
        "-assists",
    ),
    # Defense
    "defense": (
        "tackles,interceptions,clearances,blockedShots,errors,"
        "dribbledPast,aerialDuelsWon,groundDuelsWon,"
        "rating,minutesPlayed,appearances",
        "-tackles",
    ),
    # Discipline
    "discipline": (
        "yellowCards,redCards,fouls,offsides,rating,minutesPlayed,appearances",
        "-yellowCards",
    ),
    # Goalkeeper (standard)
    "keeper": (
        "saves,cleanSheets,goalsConceded,"
        "savedShotsFromInsideTheBox,savedShotsFromOutsideTheBox,"
        "goalsConcededInsideTheBox,goalsConcededOutsideTheBox,"
        "minutesPlayed,appearances",
        "-saves",
    ),
    # Goalkeeper (advanced)
    "keeper_adv": (
        "saves,cleanSheets,goalsConceded,expectedGoalsConceded,"
        "savedShotsFromInsideTheBox,savedShotsFromOutsideTheBox,"
        "goalsConcededInsideTheBox,goalsConcededOutsideTheBox,"
        "highClaims,punches,runsOut,minutesPlayed,appearances",
        "-saves",
    ),
}


def get_player_stats(
    stat_type: str = "standard",
    season: str = DEFAULT_SEASON,
    page: int = 0,
    page_size: int = 50,
) -> dict:
    sid = get_season_id(season)
    fields, order = STAT_FIELDS.get(stat_type, STAT_FIELDS["standard"])
    params = {
        "limit":        page_size,
        "order":        order,
        "accumulation": "total",
        "fields":       fields,
        "offset":       page * page_size,
    }
    data = _get(
        f"/unique-tournament/{TOURNAMENT_ID}/season/{sid}/statistics",
        params=params,
    )
    raw     = data.get("results", [])
    players = []
    for r in raw:
        p   = r.get("player", {})
        t   = r.get("team", {})
        row = {
            "player":    p.get("name"),
            "player_id": p.get("id"),
            "team":      t.get("name", ""),
            "team_id":   t.get("id"),
        }
        for k, v in r.items():
            if k not in ("player", "team"):
                row[k] = v
        players.append(row)

    return {
        "results":     players,
        "page":        page,
        "page_size":   page_size,
        "total_pages": data.get("pages"),
    }


def search_players(query: str, season: str = DEFAULT_SEASON) -> list[dict]:
    data = _get("/search/player-team-persons", params={"q": query, "sport": "football"})
    results = []
    for item in data.get("results", [])[:10]:
        e    = item.get("entity", {})
        team = e.get("team", {})
        results.append({
            "player":    e.get("name"),
            "player_id": e.get("id"),
            "team":      team.get("name", ""),
            "team_id":   team.get("id"),
            "position":  e.get("position"),
        })
    return results


# ── Top Performers ─────────────────────────────────────────────────────────

TOP_FIELDS = (
    "goals,assists,expectedGoals,expectedAssists,expectedGoalsOnTarget,"
    "yellowCards,redCards,rating,minutesPlayed,appearances,"
    "saves,cleanSheets,expectedGoalsConceded,tackles,keyPasses,"
    "totalShots,shotsOnTarget,bigChancesCreated"
)


def get_top_performers(season: str = DEFAULT_SEASON) -> dict:
    sid = get_season_id(season)

    def fetch(order: str, n: int = 10) -> list[dict]:
        params = {
            "limit":        n,
            "order":        order,
            "accumulation": "total",
            "fields":       TOP_FIELDS,
        }
        data = _get(f"/unique-tournament/{TOURNAMENT_ID}/season/{sid}/statistics", params=params)
        rows = []
        for r in data.get("results", []):
            p   = r.get("player", {})
            t   = r.get("team", {})
            row = {"player": p.get("name"), "team": t.get("name", "")}
            row.update({k: v for k, v in r.items() if k not in ("player", "team")})
            rows.append(row)
        return rows

    return {
        "top_scorers":      fetch("-goals"),
        "top_xg":           fetch("-expectedGoals"),
        "top_assists":      fetch("-assists"),
        "top_xa":           fetch("-expectedAssists"),
        "top_ratings":      fetch("-rating"),
        "top_key_passes":   fetch("-keyPasses"),
        "top_saves":        fetch("-saves"),
        "top_tackles":      fetch("-tackles"),
        "top_shooters":     fetch("-totalShots"),
    }
