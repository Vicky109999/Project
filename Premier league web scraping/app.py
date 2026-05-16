from flask import Flask, jsonify, render_template, request
from flask_caching import Cache
import scraper

app = Flask(__name__)

app.config["CACHE_TYPE"] = "SimpleCache"
app.config["CACHE_DEFAULT_TIMEOUT"] = 600
cache = Cache(app)


# ── Pages ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ── API ───────────────────────────────────────────────────────────────────────

@app.route("/api/standings")
@cache.cached(query_string=True)
def api_standings():
    season = request.args.get("season", scraper.DEFAULT_SEASON)
    return jsonify(scraper.get_standings(season))


@app.route("/api/team-stats")
@cache.cached(query_string=True)
def api_team_stats():
    season = request.args.get("season", scraper.DEFAULT_SEASON)
    return jsonify(scraper.get_team_stats(season))


@app.route("/api/players")
@cache.cached(query_string=True)
def api_players():
    stat_type = request.args.get("type", "standard")
    season    = request.args.get("season", scraper.DEFAULT_SEASON)
    page      = int(request.args.get("page", 0))
    page_size = int(request.args.get("page_size", 50))
    return jsonify(scraper.get_player_stats(stat_type, season, page, page_size))


@app.route("/api/search-players")
@cache.cached(query_string=True)
def api_search_players():
    query  = request.args.get("q", "").strip()
    season = request.args.get("season", scraper.DEFAULT_SEASON)
    if not query:
        return jsonify([])
    return jsonify(scraper.search_players(query, season))


@app.route("/api/top-performers")
@cache.cached(query_string=True)
def api_top_performers():
    season = request.args.get("season", scraper.DEFAULT_SEASON)
    return jsonify(scraper.get_top_performers(season))


@app.route("/api/seasons")
def api_seasons():
    return jsonify(list(scraper.SEASONS.keys()))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
