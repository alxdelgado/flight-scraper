# FlightSearch iOS App

SwiftUI iOS app for the Flight Price Optimizer. Requires the FastAPI backend running on Render (or locally).

---

## Requirements

- Xcode 15.2+
- iOS 17 deployment target
- macOS Sonoma or later

---

## Creating the Xcode Project

The Swift source files in `FlightSearch/` are ready to drop into a new Xcode project. Xcode project files (`.xcodeproj`) are not committed — create once locally:

**1. Open Xcode → File → New → Project**

| Setting | Value |
|---|---|
| Template | iOS → App |
| Product Name | `FlightSearch` |
| Bundle Identifier | `com.alxdelgado.FlightSearch` |
| Interface | SwiftUI |
| Language | Swift |
| Minimum Deployments | iOS 17.0 |

**2. Replace the generated files**

Delete the placeholder `ContentView.swift` and `\<AppName\>App.swift` Xcode created, then drag all files from the `FlightSearch/` folder into the Xcode project navigator.

**3. Set the deployment target**

Project → Targets → FlightSearch → General → Minimum Deployments → **iOS 17.0**

---

## Project Structure

```
FlightSearch/
├── FlightSearchApp.swift          @main entry point
├── Config.swift                   API base URL (debug vs release)
├── Models/
│   ├── Airport.swift              Airport + response wrappers
│   ├── Flight.swift               Individual flight leg
│   ├── Candidate.swift            Ranked trip candidate (RT or two-OW)
│   └── SearchModels.swift         Request / response / history models
├── Services/
│   └── NetworkService.swift       All API calls (async/await + URLSession)
├── ViewModels/
│   └── SearchViewModel.swift      @Observable state machine for search flow
└── Views/
    └── ContentView.swift          Root view (placeholder — Feature 5 adds screens)
```

---

## Running Against Local Backend

```bash
# Terminal 1 — start the API
cd /path/to/flight-scraper
source .venv/bin/activate
uvicorn server:app --reload --port 8000
```

`Config.swift` automatically points to `http://localhost:8000` in `DEBUG` builds and `https://flight-price-optimizer.onrender.com` in `RELEASE` builds.

---

## Running Against Render (Production)

No changes needed — the `RELEASE` scheme targets the production URL automatically. Build for release or set the active scheme to **Release** in Xcode.

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| `@Observable` (iOS 17) | Eliminates `@Published` boilerplate, integrates cleanly with SwiftUI |
| `async/await` throughout | No Combine chains — simpler polling loop, easy to reason about |
| No third-party dependencies | `URLSession` + Swift Concurrency covers all networking needs for MVP |
| `SearchPhase` enum | Explicit state machine prevents impossible UI states (e.g. showing results while still searching) |
| `NetworkService` as injectable | Pass a test double in unit tests without hitting the real API |
