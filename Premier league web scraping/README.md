# Premier League Stats Tracker

A local web app that fetches live Premier League statistics from Sofascore and displays them in a modern dashboard.

## Features

- **League Table** — Full standings for any season with colour-coded zones (Champions League / Europa / Conference / Relegation)
- **Team Stats** — Detailed squad stats: goals, assists, shots, possession, pass accuracy, tackles, clean sheets, cards
- **Player Stats** — All players with 6 stat categories (Standard, Shooting, Passing, Defense, Discipline, Goalkeepers). Paginated (50 per page) with name/team search
- **Top Performers** — Top 10 leaderboards for goals, assists, ratings, saves, and tackles
- **Season Switcher** — Toggle between 25/26, 24/25, and 23/24 seasons from the header
- **10-minute cache** — Responses are cached so repeated refreshes are instant

## Quick Start

### 1. Install dependencies

Open a terminal in this folder:

```
C:\Users\Vicky109\anaconda3\python.exe -m pip install -r requirements.txt
```

### 2. Run the app

```
C:\Users\Vicky109\anaconda3\python.exe app.py
```

### 3. Open in browser

Visit: **http://localhost:5000**

> The first load for each section takes 2–5 seconds while data is fetched. Subsequent loads within 10 minutes are instant from cache.

## File Structure

```
schdule tool/
├── app.py              # Flask server & API routes
├── scraper.py          # Sofascore API data fetching
├── requirements.txt    # Python dependencies
├── README.md
└── templates/
    └── index.html      # Frontend dashboard (single-page app)
```

## Data Source

All data is fetched from the Sofascore API. This tool is for personal use only.
