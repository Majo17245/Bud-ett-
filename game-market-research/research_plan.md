# Research plan (as executed)

Date of research: 2026-10-08. Window: games released ~April 2025 – October 2026 (older titles only if they had a viral resurgence; flagged).

1. Benchmark: "How to Fish" (Dazed Games) — verify title, dev, platforms, release date, price, sales, CCU via Steam store, SteamDB, press, dev posts.
2. Discovery: SteamDB peak-CCU charts + Steam top sellers + press round-ups (“sold 1 million copies”, “friendslop”, “solo developer hit”), Roblox top experiences, AppMagic/Sensor Tower press for mobile, Poki/CrazyGames/itch.io top lists, TikTok/Twitch virality coverage.
3. Parallel data collection: subagents research ~5 games each and write one JSON per game into `data/` (progress saved continuously).
4. Estimation rules:
   - Steam units: Boxleiter = reviews × multiplier (30–60; multiplier chosen per game and stated).
   - Net revenue = gross × 0.70 (store cut) × ~0.85–0.90 (refunds, regional pricing, VAT/sales-tax leakage); stated per game.
   - Dev cost = team size × months × assumed monthly cost per person (country-adjusted), unless the dev disclosed it.
   - Every number tagged [CONFIRMED] (dev/publisher/official) or [ESTIMATE] (method stated). Missing = "no data".
5. Cross-check key numbers in ≥2 independent sources; reconcile conflicts before writing the report.
6. Deliverables: `games_analysis.xlsx` (+ `games_analysis.csv`), `report.md`.
