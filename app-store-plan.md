# Flight Price Optimizer — App Store Plan

**Status:** In development  
**Target platform:** iOS (App Store)  
**Backend:** Python / FastAPI on Render  
**Last updated:** 2026-05-13

---

## Overview

The Flight Price Optimizer script is being converted into a hosted iOS app. The Python search engine, pricing algorithm, and booking link generator remain unchanged — they are wrapped in a REST API that a Swift/SwiftUI iOS app calls.

---

## Architecture Decisions

### Hosting — Render (Free Web Service)

**Decision made by:** CFO Advisor + CTO Advisor  
**Date:** 2026-05-13

**Rationale:**
- $0 cost, no credit card required — correct burn rate for zero users
- Native Python/FastAPI support, no Docker required for deployment
- Free PostgreSQL tier (1GB) included on same platform
- GitHub push → auto-deploy, zero DevOps overhead
- Cold start (~30s) is irrelevant: searches already take 2–5 minutes
- One `Dockerfile` away from migrating to Railway, Fly.io, or Cloud Run when users arrive

**Rejected options:**
- Railway — requires credit card, $5/month after free credit expires
- Vercel — 60-second function timeout shorter than a full search run
- Fly.io — free but requires Docker + flyctl CLI config overhead
- Google Cloud Run — free at scale but highest setup complexity for MVP

**Future migration trigger:** First paying user or 100 searches/month, whichever comes first.

### Database — PostgreSQL on Render (Free Tier)

**Decision:** Replace SQLite with PostgreSQL for Render compatibility.  
**Free tier:** 256MB RAM, 1GB storage — sufficient for MVP search history.  
**Fallback:** Supabase free tier (500MB) if Render DB hits storage limit.

### Async Search Pattern — Polling

**Decision:** POST `/search` returns a `search_id` immediately. Client polls `GET /search/{id}` until status is `complete`.  
**Rationale:** Simplest pattern for MVP. No WebSocket infrastructure required.  
**Upgrade path:** WebSocket streaming (v1.1) so results appear airport-by-airport as sessions complete.

### iOS Stack — SwiftUI

**Decision:** SwiftUI + Swift Concurrency (`async`/`await`) + URLSession.  
**No third-party dependencies for MVP.**  
**Minimum deployment target:** iOS 17

---

## Live Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     iOS App (SwiftUI)                       │
│                                                             │
│  SearchView → AirportPickerView → ResultsView → WinnerView  │
│       │                                   │                 │
│  NetworkService (URLSession + async/await) │                 │
└───────────────────────┬───────────────────┘                 │
                        │ HTTPS / JSON                        │
┌───────────────────────▼─────────────────────────────────────┐
│              Render — Python FastAPI (server.py)            │
│                                                             │
│  POST /search          → enqueue background search task     │
│  GET  /search/{id}     → poll status + partial results      │
│  GET  /airports        → airport registry (resolve query)   │
│  GET  /history         → past search winners                │
│                                                             │
│  Background worker (ThreadPoolExecutor):                    │
│    airports.py → api_client.py → price_optimizer.py         │
│    → storage.py (PostgreSQL)                                │
└──────────────┬────────────────────────┬─────────────────────┘
               │                        │
   ┌───────────▼──────────┐  ┌──────────▼──────────┐
   │  SerpAPI             │  │  PostgreSQL          │
   │  (Google Flights)    │  │  (Render free tier)  │
   └──────────────────────┘  └─────────────────────-┘
```

---

## API Specification

### POST `/search`
Start an async flight search.

**Request body:**
```json
{
  "origin": "ORD",
  "destination": "NYC",
  "depart_date": "2026-06-15",
  "return_date": "2026-06-20",
  "max_destinations": 10
}
```

**Response:**
```json
{
  "search_id": "uuid",
  "total_sessions": 9,
  "status": "running"
}
```

---

### GET `/search/{search_id}`
Poll for search status and results.

**Response (running):**
```json
{
  "search_id": "uuid",
  "status": "running",
  "completed_sessions": 4,
  "total_sessions": 9
}
```

**Response (complete):**
```json
{
  "search_id": "uuid",
  "status": "complete",
  "completed_sessions": 9,
  "total_sessions": 9,
  "winner": {
    "type": "two-one-ways",
    "label": "ORD→EWR / JFK→ORD",
    "listed_price": 312.00,
    "baggage_cost": 0.00,
    "effective_price": 312.00,
    "savings": 17.00,
    "savings_vs": "round-trip",
    "outbound": {
      "airline": "United",
      "origin": "ORD",
      "destination": "EWR",
      "price_usd": 149.00,
      "stops": 0,
      "duration_mins": 140,
      "departure_time": "08:00",
      "arrival_time": "10:20",
      "booking_url": "https://www.google.com/travel/flights?tfs=..."
    },
    "return": {
      "airline": "JetBlue",
      "origin": "JFK",
      "destination": "ORD",
      "price_usd": 163.00,
      "stops": 0,
      "duration_mins": 175,
      "departure_time": "14:00",
      "arrival_time": "16:55",
      "booking_url": "https://www.google.com/travel/flights?tfs=..."
    }
  },
  "ranked": [...]
}
```

---

### GET `/airports?q={query}`
Resolve an airport query. Accepts IATA code, metro alias, city name, or region.

**Response:**
```json
{
  "query": "NYC",
  "airports": [
    {"iata": "JFK", "name": "John F. Kennedy International", "city": "New York", "subdivision": "NY", "is_international": true},
    {"iata": "LGA", "name": "LaGuardia", "city": "New York", "subdivision": "NY", "is_international": false},
    {"iata": "EWR", "name": "Newark Liberty International", "city": "Newark", "subdivision": "NJ", "is_international": true}
  ]
}
```

---

### GET `/history?limit={n}`
Return the most recent search winners.

**Response:**
```json
{
  "runs": [
    {
      "id": 1,
      "run_at": "2026-05-13T14:22:10Z",
      "origin": "ORD",
      "destination": "NYC",
      "depart_date": "2026-06-15",
      "return_date": "2026-06-20",
      "winner_type": "two-one-ways",
      "winner_price": 312.00
    }
  ]
}
```

---

## iOS App Screens

| Screen | Key elements |
|---|---|
| **Search** | Origin/destination text fields, date pickers, Search button |
| **Airport Picker** | Search field → calls `GET /airports?q=`, shows resolved list with IATA + city |
| **Searching** | Progress bar + "Searching 4 of 9 airports…" label, polls every 2s |
| **Results** | Ranked table: effective price, route, stops, bags indicator |
| **Winner Detail** | Full breakdown: listed vs effective, baggage line, savings vs alternative, Book button(s) |
| **History** | List of past searches with winner type and price |
| **Settings** | Carry-on / checked bag toggles, stops penalty slider |

---

## Feature Implementation Queue

Implemented sequentially. Each feature is reviewed, committed, and pushed before the next begins.

| # | Feature | Files | Status |
|---|---|---|---|
| 1 | FastAPI server with polling search, airports, and history endpoints | `server.py`, `requirements.txt`, `Procfile` | 🔲 |
| 2 | PostgreSQL migration — replace SQLite driver | `storage.py`, `.env.example`, `requirements.txt` | 🔲 |
| 3 | Render deployment config | `render.yaml`, `README.md` | 🔲 |
| 4 | Swift iOS project scaffold — NetworkService + models | `ios/` | 🔲 |
| 5 | SwiftUI Search + Airport Picker screens | `ios/` | 🔲 |
| 6 | SwiftUI Searching (polling) + Results screens | `ios/` | 🔲 |
| 7 | SwiftUI Winner Detail + Book button | `ios/` | 🔲 |
| 8 | SwiftUI History + Settings screens | `ios/` | 🔲 |
| 9 | App Store assets — icon, screenshots, privacy policy | `ios/`, `AppStore/` | 🔲 |

---

## App Store Requirements

| Item | Detail |
|---|---|
| Apple Developer Account | $99/year — required before submission |
| iOS minimum target | iOS 17 |
| App category | Travel |
| Privacy policy | Required — discloses SerpAPI / Google Flights data usage |
| App Transport Security | HTTPS only — Render enforces this |
| App Review turnaround | 24–48 hours typical |
| In-app purchases | None for MVP |

---

## Product Roadmap

### MVP — v1.0
- FastAPI backend on Render
- SwiftUI app: Search, Results, Winner Detail, Book button
- Polling progress during search
- App Store submission

### v1.1
- WebSocket streaming — results appear airport by airport
- Search history screen
- Settings (baggage toggles, stop penalty)

### v2.0
- Push notifications via APNs (search in background, notify on complete)
- Price alerts — watch a route, notify on drop
- iPad / Mac Catalyst
- Apple Sign In for multi-user history sync

---

## Cost Summary

| Item | Cost |
|---|---|
| Render web service | Free |
| Render PostgreSQL | Free |
| SerpAPI (< 100 searches/month) | Free |
| Apple Developer Account | $99/year (required at submission) |
| **Total until App Store submission** | **$0** |
