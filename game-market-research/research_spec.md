# Research spec for per-game data collection (shared by all research agents)

Research date: **2026-10-08**. Window: games released **~April 2025 – October 2026**. Older games only if they had a
major viral resurgence in that window (flag clearly).

## Environment constraints
- `WebFetch` and `curl` are BLOCKED by the network policy (DNS/proxy refusal for steampowered.com, steamdb.info,
  gamalytic.com, wikipedia.org, etc.). Use **WebSearch only**. It returns a summary plus source URLs.
- Get page-specific data by targeting domains with `allowed_domains`, e.g.
  `["steamdb.info"]`, `["gamalytic.com"]`, `["vginsights.com"]`, `["steampageanalyzer.com","raijin.gg","steampulse.org"]`,
  `["store.steampowered.com"]`, `["rolimons.com","romonitorstats.com"]`, `["appmagic.rocks","sensortower.com","foxdata.com"]`,
  `["newsletter.gamediscover.co"]`, `["gamesradar.com","pcgamer.com","gamedeveloper.com","rockpapershotgun.com"]`.
- Use `mode: "standard"` by default; use `"extended"` for niche/recent facts, or when standard results are thin.
- Do **3–5 separate searches per game** before concluding a data point is unavailable.
- Cross-check key numbers (units sold, revenue, downloads, peak CCU) in **≥2 independent sources** where possible.

## Labelling rules (mandatory)
Every number gets a tag:
- `[CONFIRMED]`: stated by the developer, the publisher or an official platform source (a Steam news post, a dev tweet quoted by press,
  a platform press release). Name the source briefly, e.g. "1,000,000 copies by 2026-08-22 [CONFIRMED – dev Steam post via Inven Global]".
- `[ESTIMATE]`: computed or inferred, or taken from a third-party tracker (Gamalytic, VG Insights, Alinea, SteamSpy,
  Raijin, Steam Page Analyzer, AppMagic, Sensor Tower). State the method or tracker briefly.
- If nothing can be found, write `"no data"`. **Never invent numbers.** Always give the date a figure refers to.

## Estimation methods (use these so all games are comparable)
1. **Units (Steam), Boxleiter method:** units ≈ total reviews × multiplier. State the multiplier and why.
   - Default 40 for typical 2025–26 premium indies.
   - 30 for niche/enthusiast or single-player games with an engaged community (high review propensity).
   - 50–60 for cheap (<$10) mass-market or viral co-op/party games bought in multi-packs or gifted, and for games with a large
     Chinese audience. Mega-viral friendslop has shown implied ratios of 60–100+.
   - **Calibration:** if a CONFIRMED unit figure AND a review count from around the same date both exist, report the
     *implied ratio* (units ÷ reviews). This is valuable; always include it when possible.
2. **Gross revenue:** units × average realised price. Average realised price ≈ US list price × 0.75 (regional
   pricing, launch discounts, bundles) unless better info exists. If Gamalytic/VG Insights/Alinea publish a gross revenue
   estimate, report it as well, labelled with its source.
3. **Net revenue (to developer+publisher, before income tax):** gross × (1 − store cut) × 0.93 (refunds/chargebacks).
   - Steam cut: 30% on the first $10M of a game's gross, 25% on $10M–$50M, 20% above $50M.
   - Apple/Google: 15% under $1M/yr (small business programs), otherwise 30%. Ad revenue: report the network/portal share.
   - Roblox: creators keep ~70% of Robux spent in their experience (game passes/dev products); DevEx pays ≈ $0.0038 per Robux
     (2025 rate). Net to the creator ≈ 25–30% of consumer spend. Use reported earnings if any exist.
   - Browser portals (Poki/CrazyGames): ad revenue share (Poki ~50% of portal-sourced traffic; CrazyGames ~60% ads/70% IAP per
     2026 terms) — state what you used.
   - If a publisher is involved, note that the dev/publisher split is unknown unless reported.
4. **Production cost:** use a disclosed figure if one exists. Otherwise team size × months × monthly cost per person:
   ~$6k (US/W. Europe/Japan/Australia lean indie), ~$3k (E. Europe/LatAm/SE Asia/China/Uzbekistan etc.), plus a
   publisher/marketing note if relevant. A solo dev who worked unpaid has an *opportunity cost*; say so.
5. **AI feasibility score (1–5)**, i.e. how easily ONE person using AI tools (Claude Code, AI image/3D/audio generators) could build a
   *similar* game (not a copy):
   - 5 = simple 2D/low-poly, single-player or async, one core loop, small content → MVP in ≤4 weeks.
   - 4 = simple 3D + physics, or light/peer-hosted multiplayer (Steam lobbies, Photon/Fishnet/Netcode), modest content → 1–3 months.
   - 3 = real-time online multiplayer with lots of physics/sync, many interlocking systems, or a high "feel"/polish bar → 3–6 months.
   - 2 = heavy hand-crafted content, high art/animation bar, deep systems → 6–18 months.
   - 1 = not realistic solo (huge content, live-ops MMO-scale backend, AAA art).
   Justify with: what AI handles well (code, 2D/3D assets, SFX, music, text/dialogue), what AI cannot replace (design,
   game feel, balancing, playtesting, marketing, community), and a concrete toolset (e.g. "Claude Code + Godot 4 +
   Steamworks.NET/GodotSteam, Scenario/Midjourney/Retro Diffusion for 2D, Meshy/Tripo for 3D, ElevenLabs SFX, Suno/Udio music").
6. **Solo+AI build cost/time:** MVP and polished version. Include tool subscriptions (Claude Pro/Max $20–$200/mo, image gen $10–$60/mo,
   3D gen $20–$60/mo, audio $10–$30/mo), Steam Direct fee $100, Apple $99/yr, Google $25 once, asset packs, optional
   freelance polish, playtest/marketing budget. Give a time range in weeks/months and a cash range in USD. Exclude the developer's own living costs (say so).

## Output: one JSON file per game
Write to: `/home/user/Bud-ett-/game-market-research/data/<ID>_<slug>.json` (e.g. `B01_how-to-fish.json`).
Write each file **as soon as that game is done** (progress must be saved). Valid JSON, UTF-8, string values (except score).

```json
{
  "id": "B01",
  "group": "A or B",
  "title": "",
  "genre": "genre / subgenre",
  "release_date": "YYYY-MM-DD (full release or launch) + platform if it differs",
  "early_access_date": "YYYY-MM-DD or 'n/a'",
  "window_note": "in window / outside window (reason it is included)",
  "developer": "studio or person",
  "team_size": "number + source/label",
  "country": "",
  "developer_background": "first game? previous hits? how the team formed",
  "publisher": "name or 'self-published'",
  "platforms_and_store_links": "Steam: https://store.steampowered.com/app/... ; Switch: ... ; etc.",
  "business_model": "premium $X (launch discount), F2P + IAP, ads, DLC, Roblox passes, etc.",
  "price_usd": "",
  "units_or_downloads": "with labels and dates",
  "peak_concurrent_players": "with labels and dates",
  "steam_reviews": "count, % positive, date (or 'n/a' for non-Steam)",
  "implied_review_multiplier": "units ÷ reviews if both known at similar dates, else 'n/a'",
  "gross_revenue": "with label + method",
  "net_revenue": "with label + method",
  "production_cost": "with label + method",
  "development_time": "with label",
  "why_popular": "hook, core mechanic, emotional/social appeal",
  "marketing_channels": "TikTok / YouTube / Twitch streamers / Next Fest demo / Reddit / word of mouth / timing / price",
  "engine": "with label",
  "art_style": "",
  "ai_feasibility_score": 3,
  "ai_feasibility_justification": "AI can: … | AI cannot: … | Toolset: …",
  "solo_ai_mvp_cost_time": "e.g. 3–5 weeks, $150–$400",
  "solo_ai_polished_cost_time": "e.g. 4–7 months, $1,500–$6,000",
  "sources": [{"title": "", "url": ""}],
  "data_conflicts": "where sources disagree and what you chose",
  "notes": "anything else useful for a solo creator"
}
```
Include at least 4–8 sources per game (store page + tracker + 2+ press/dev sources).
