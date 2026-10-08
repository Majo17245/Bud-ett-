# Viral Indie Game Market Scan, Apr 2025 – Oct 2026
### Benchmark: *How to Fish* (Dazed Games, 2026). Focus: which recent hits a solo creator could realistically recreate with AI tools

Research date: **8 October 2026**. Deliverables in this folder:

| File | What it is |
|---|---|
| `games_analysis.xlsx` | One row per game (35 games). The "Games" sheet has every requested data point plus Sources and Group. There is also a sortable "Summary (numeric)" sheet, a "Sources" sheet (one row per URL) and a "Methodology" sheet. |
| `games_analysis.csv` | Same content as the "Games" sheet. |
| `data/*.json` | Raw per-game research files, the master data the spreadsheet is built from. |
| `data/_market_stats.md` | Market statistics used in the risk section, every figure cited. |
| `research_plan.md`, `research_spec.md` | Research plan, estimation rules and labelling rules. |
| `build_spreadsheet.py`, `summary_numbers.json` | Script that rebuilds the spreadsheet; best-estimate numbers for the summary sheet. |

**Labels.** Every number in the data files carries a label:
- **[CONFIRMED]** means a developer, publisher or platform said it.
- **[ESTIMATE]** means it is a tracker figure or my own calculation, and the method is stated.
- Missing data is written as "no data".

In this report, figures follow the same convention: "[C]" means confirmed and "[E]" means estimate. The dates of figures matter because many of these games are still selling.

---

## 1. Executive summary

**The market in one paragraph.** From April 2025 to October 2026, the biggest money in indie games went to two kinds of game:
1. Cheap online co-op "friendslop" with one comedic hook, from teams of 2–7 people. Examples: *PEAK*, *RV There Yet?*, *Meccha Chameleon*, *How to Fish*, *Gamble With Your Friends*, *Machine Party*.
2. Roguelites built on a "numbers go up" hook. Examples: *Megabonk*, *BALL x PIT*, *CloverPit*, *Slay the Spire 2*, *Mewgenics*.

Beside them sit the long-cycle craft hits (*Silksong*, *Blue Prince*, *Big Walk*) and an enormous, very top-heavy Roblox meme-simulator economy (*Grow a Garden*, *Steal a Brainrot*, *99 Nights in the Forest*). Steam is flooded: 20,282 releases in 2025 and 20,220 more by 1 Oct 2026. The median 2025 release grossed about **$249**, so the distance between a hit and everyone else is extreme.

### Key trends

1. **Tiny teams made the biggest hits.** Six of the 11 Group A hits had five or fewer core people:
   - *Meccha Chameleon*: 2 people, 20M copies [C].
   - *Megabonk*: 1 person, about 5.3M [E].
   - *RV There Yet?*: 4 people, 4.5M+ [C].
   - *Escape from Duckov*: 5 people, 3M+ [C].
   - *Silksong*: 3 core, 7M+ [C].
   - *Mewgenics*: 2 core, 1M in a week [C].

   *PEAK* (7 people) cost **under $200k** to make [C].
2. **Speed beats polish for the viral path.**
   - *Meccha Chameleon*: about 2 months.
   - *RV There Yet?*: just over 2 months.
   - *PEAK*: core built in a 4-week jam, about 4 months in total.
   - *Grow a Garden*: about 3 days for the original.
   - *99 Nights in the Forest*: about one week.

   The craft path takes 4–8 years (*Silksong*, *Blue Prince*, *Mewgenics*, *Big Walk*, *Baby Steps*, *Tangy TD*). For one person using AI, the fast path is the realistic one.
3. **Friendslop is the dominant 2025–26 format.** Online co-op for 2–6 friends, at $5–10, with physics comedy, an optional proximity-voice gimmick and short sessions. Genre-wide concurrent players hit a record **~350k in June 2026** [E]. Each hit fades from more than 50% of the genre's players to about 10% within 3–9 months [E – How To Market A Game].
4. **The $7.99 price with a 38% launch discount to $4.95 is now a template.** *PEAK*, *How to Fish*, *Sledding Game*, *Gamble With Your Friends* and *BOMBANANA!* all used it. 16 of the 25 paid games in Groups A and B cost **$9.99 or less**.
5. **The hook is explainable in one sentence and produces a funny clip within 60 seconds.**
   - "Paint yourself to hide."
   - "Shoot the fish you catch."
   - "Push an RV up a mountain with friends."
   - "Three monkeys, one blind, one deaf, one mute, defuse a bomb."
6. **Recurring themes:**
   - **Animals:** cats, ducks, monkeys, chameleons.
   - **Gambling** with no real money: *CloverPit*, *Gamble With Your Friends*, *BidKing*, and gambling your catch in *How to Fish*.
   - **Fishing:** *How to Fish*, *Cast n Chill*, *Webfishing*.
   - **Desktop companions:** *Bongo Cat*, *Cast n Chill*, *Desktop Defender*.
   - **Voice-driven play:** *YAPYAP*, *Mage Arena*, *Big Walk*.
   - **Meme culture:** "Italian brainrot".
7. **Art styles are cheap and readable.**
   - Stylised low-poly 3D: *PEAK*, *How to Fish*, *Megabonk*, *RV There Yet?*, *Sledding Game*, *Meccha Chameleon*.
   - PSX-style lo-fi: *YAPYAP*, *CloverPit*, *Machine Party*.
   - Pixel art: *BALL x PIT*, *Cast n Chill*, *Tangy TD*.

   High-end art shows up mostly in the long-cycle craft hits.
8. **Engines.** Unity is the most common: *Silksong*, *PEAK*, *Megabonk*, *Blue Prince*, *BALL x PIT*, *YAPYAP*, *Sledding Game*, and *How to Fish* (inferred). Godot is rising: *Slay the Spire 2* moved to it, and *Project P.I.T.T.* likely uses it. Unreal 5 powers *Meccha Chameleon* (datamined) and *RV There Yet?*. A custom engine is the exception (*Mewgenics*, *Tangy TD*).
9. **Marketing is organic, not paid.** *Meccha Chameleon* spent **$0 on ads** [C]. *How to Fish* posted **weekly TikTok devlogs** for months [C]. Other channels that worked:
   - Steam Next Fest demos: *BOMBANANA!*, *YAPYAP*, *Desktop Defender*, *Megabonk*, *BALL x PIT*.
   - Big YouTubers: *Project P.I.T.T.*
   - The developer's own Twitch audience: *Tangy TD*.
   - VTubers: *Agreeee*.
   - A label halo: Landfall for *How to Fish*, Devolver, Panic.
10. **Review-based sales estimates break for cheap viral games.** Units per Steam review:

    | Game | Units per review |
    |---|---|
    | *Silksong* | ~15–25 |
    | *PEAK* | ~31–34 |
    | *How to Fish* (at its 1M milestone) | ~80 |
    | *YAPYAP* | 125–190 |
    | *Meccha Chameleon* | ~220 |
    | *Machine Party* | 240–280 |

    Third-party trackers (Raijin, Steam Page Analyzer) undercounted several of these hits by 2–5×.
11. **Reach is not revenue.**
    - *Bongo Cat* had about 194k concurrent players and earned about **$3k/month** [C].
    - *Baby Steps* had heavy streamer buzz and roughly 50–100k copies [E].
    - Mobile top charts are dominated by paid-UA machines. *Meowdoku!* reportedly spent about $500k a day on ads [E].
12. **AI is mainstream but carries stigma.**
    - About 31% of 2026 Steam releases disclose AI use, yet they take only about 10–27% of sales [E].
    - About 25% of US players say AI use makes them less likely to buy [E].
    - Since January 2026, Steam no longer requires disclosure for behind-the-scenes coding tools [C]. Visible AI art is where backlash concentrates.

### Bottom line for you

A solo creator using AI can realistically build the *type* of game that won in 2025–26:
- a small online co-op party game, or
- a single-player roguelite with a gambling or "numbers go up" hook, or
- a desktop idle companion, or
- a Roblox collection simulator.

Each takes 2–10 weeks to reach an MVP. What AI does not supply is the parts that actually separate hits from the median $249 release: a sharp hook, game feel, many group playtests, and months of audience-building before launch.

---

## 2. Benchmark deep dive: *How to Fish*

### 2.1 Verified facts

| Item | Value |
|---|---|
| Exact title | **How to Fish** (Steam app 4001890) |
| Genre | Online co-op physics fishing / comedic shooter ("friendslop"), 1–4 players. Lobbies went up to 8 in patch 1.0.4. |
| Developer | **Dazed Games**, Skövde/Gothenburg, **Sweden**. Founders Carl-Vilhelm Johansson and Melvin Olsson. **2 people** [C]. |
| Background | Met at high school in Gothenburg. Their student game *Out of Hand* went viral in China (~180–200k players) [C]. A paid online version (2025) sold "significantly lower than hoped"; "we weren't good at marketing" [C]. They joined the Science Park Skövde startup programme. |
| Publisher | Self-published on Steam, with a **project investment from Evil Landfall** (the investment arm of *PEAK*/*Content Warning* studio Landfall). No equity was taken [C]. |
| Platforms | Steam (PC, Steam Deck Verified). Console and Mac versions are planned, no date [C]. |
| Release | **20 Aug 2026** (full release, no Early Access) [C] |
| Price | **$7.99**, with a **38% launch discount to $4.95** until 27 Aug [C] |
| Sales | **1,000,000 copies in ~48 hours** (22 Aug) [C – dev Steam post]. **6.3M+ units sold in August alone** [E – GameDiscoverCo August readout, corroborated by secondary reports]. A later GameDiscoverCo figure of >8.5M by the end of September is reported but could not be re-verified [E]. The developers had hoped for ~200k [C]. |
| Peak concurrent players | **373,971** (~25/26 Aug 2026) [C – SteamDB]. Progression: about 22k on day 1, 268,101 on 23 Aug, 341,691 on 24 Aug. |
| Reviews | ~12–13k at the 1M milestone. **61,145 (95% positive) on 12 Sep. ~69k (95%) in late September.** |
| Units per review | **~80 at the 1M milestone**, rising to ≥100 later [E] |
| Gross revenue | **~$26M on Steam in August alone** (about $4.1 per unit), up to ~$38M by the end of September (unverified) [E – GameDiscoverCo] |
| Net revenue | **~$18–26M** after Steam's tiered cut and refunds, shared between Dazed Games and Evil Landfall (split undisclosed) [E] |
| Production cost | ~**$144k** (2 people × 12 months × $6k) [E]. No paid marketing reported. |
| Development time | **~12 months** (Aug 2025 → Aug 2026) [C] |
| Engine / art | **Unity 6** (inferred from a player's crash report) [E]. Stylised low-fi first-person 3D, bright islands, cartoon creatures. |
| Post-launch | Patches for 8-player lobbies, private lobbies and cloud saves. **v1.1.0 "Islet Update" on 28 Sep** (new islands, mini-boss, bow, new creatures) and a **PEAK + How to Fish bundle** [C]. |

Sources: [Steam news "1 MILLION FISHERMEN IN 2 DAYS"](https://store.steampowered.com/news/app/4001890/view/711158520539514065); [GamesRadar – 1M in 2 days](https://www.gamesradar.com/games/co-op/latest-steam-lottery-winner-how-to-fish-sells-1-million-copies-in-2-days-yes-well-be-adding-more-content/); [GamesRadar – 370k peak](https://www.gamesradar.com/games/co-op/amid-the-friendslop-renaissance-usd5-co-op-fishing-game-hits-370-000-peak-players-on-steam-in-5-days/); [GameDiscoverCo – August 2026's top new games](https://newsletter.gamediscover.co/p/august-2026s-top-new-pc-and-console); [Cinevva summary of the GameDiscoverCo August data](https://app.cinevva.com/news/2026-09-04-how-to-fish-august-indie-sales); [Sweden Game Arena – 1M in 2 days](https://swedengamearena.com/en/news/dazed-games-hits-one-million-copies-sold-just-two-days/); [Sweden Game Arena – project investment](https://swedengamearena.com/en/news/dazed-games-secures-project-investment-and-sets-sights-2026-launch/); [Sweden Game Arena – Out of Hand](https://swedengamearena.com/en/news/party-game-drew-180000-players-worldwide-now-a-new-version-launches/); [Game World Observer – Evil Landfall](https://gameworldobserver.com/2026/04/08/the-authors-of-peak-and-content-warning-have-launched-their-own-publishing-house); [Streams Charts – How to Fish](https://streamscharts.com/games/how-to-fish). The full list of 25 sources is in the spreadsheet.

### 2.2 Timeline

- **Aug 2025:** after the failed paid launch of *Out of Hand*, the duo starts *How to Fish*.
- **Autumn 2025 – summer 2026:** weekly short TikTok/Instagram "feature" videos. By the time they pitched Landfall they had several million views and a Discord of about 1,300 members [C].
- **By April 2026:** project investment from Evil Landfall announced, signed about a week after meeting at a Berlin trade fair [C]. At that point the target launch was "end of 2026".
- **20 Aug 2026:** launch at $4.95. There was no public demo or playtest beforehand.
- **22 Aug:** 1M copies sold.
- **23–26 Aug:** concurrent players climb from 268k to a 374k peak, around fourth place on Steam. Press snowballs ("Steam lottery winner").
- **Week 1:** Twitch streamers, led by TheBurntPeanut with about 331k hours watched [E – Streams Charts], plus many small group streams.
- **28 Sep:** first content update and the PEAK bundle.

### 2.3 Why it worked

1. **A clear reversal hook.** A calm fishing game turns into chaos: you catch absurd sea creatures, then shoot, punch or dynamite them; gamble your catch; fight seagulls and boss fish. The joke is understood in one clip.
2. **A proven format.** It uses the 1–4 friend co-op "friendslop" template that *Lethal Company*, *R.E.P.O.* and *PEAK* had already taught Steam's algorithm and streamers to push. It combines *Webfishing*'s social fishing (2024; ~70k reviews, 97% positive [E]) with *PEAK*-style physics comedy.
3. **An impulse price plus group buying.** At $4.95, one friend convinces three more. That is why about 80 units were sold per review at the 1M mark.
4. **An audience built before launch.** Months of weekly devlog clips, and a Discord community.
5. **The Landfall halo.** Credibility, Landfall's channels, and a PEAK bundle. This is the "publisher-light" model: investment without giving up the studio.
6. **Timing.** Late summer holidays, during a friendslop wave that *Meccha Chameleon* (June) and *Machine Party* (July) had kept hot.
7. **Fast follow-up.** Daily patches, then a content update within 5 weeks, while attention was still high.

### 2.4 What a solo, AI-assisted creator can copy, and what not

| Copyable with AI | Not solved by AI |
|---|---|
| Core code for a host-authoritative co-op game (Steam lobbies, P2P), shooting, a fish AI, an economy, an upgrade shop | Making physics fun and *in sync* across 2–4 players with real internet lag. This is the hardest part, and the duo needed 12 months. |
| Low-poly creatures and props (Meshy/Tripo), SFX (ElevenLabs), music (Suno), UI text, Steam page copy | The comedic tuning: which gun, which fish, which ragdoll moment produces laughter. That needs dozens of group playtests. |
| A content pipeline (new fish and weapons as data) | Months of consistent short-video marketing, and the Landfall relationship |

**AI feasibility: 3/5.** A solo MVP of a *similar-in-spirit* game takes 6–10 weeks and about $300–900 in tools; a polished version takes 6–10 months and about $3k–12k (excluding living costs).

**Scope-down advice for a How to Fish-like:**
- 1 island
- 6 creatures
- 3 weapons
- 1 boss
- a sell-and-upgrade shop
- Steam-lobby P2P for 2–4 players, with no dedicated servers

Ship a free Steam Playtest or demo early to get the group playtesting the original team skipped. Section 5, option 2, gives an original idea built on the same recipe.

---

## 3. The games at a glance

Full detail for every game (12 data points, sources and conflicts) is in `games_analysis.xlsx`.

**Group definitions:**
- **Group A** (11 games): the biggest indie hits of the window, from studios of up to ~20 people.
- **Group B** (20 games): small viral games from teams of 1–5 people, similar in spirit to *How to Fish*.
- **Group C** (4 games): **context cases**. They were popular, but their team size could not be verified as ≤5 or turned out to be large. They are kept for comparison and not counted in Group B.

### Group A – biggest indie hits

| ID | Game | Team | Release | Price | Units / players (M) | Peak CCU (k) | Gross (US$M) | AI score |
|---|---|---|---|---|---|---|---|---|
| A01 | Hollow Knight: Silksong | 3 core + contractors | 2025-09-04 | $19.99 | 7 [C] | 587.2 | 105 [E] | 2 |
| A02 | Slay the Spire 2 | ~10 core | 2026-03-05 (EA) | $24.99 | 7.1 [E] | 574.6 | 133 [E] | 4 |
| A03 | PEAK | 7 | 2025-06-16 | $7.99 | 11 [E] | 170.8 | 62 [E] | 3 |
| A04 | Meccha Chameleon | 2 | 2026-06-10 | $5.99 | 20 [C] | 340.5 | 66 [E] | 4 |
| A05 | Escape from Duckov | 5 | 2025-10-16 | $17.99 | 3.8 [E] | 301.3 | 45 [E] | 3 |
| A06 | Megabonk | 1 | 2025-09-18 | $9.99 | 5.3 [E] | 117.3 | 40 [E] | 4 |
| A07 | Mewgenics | 2 core + artist + composer | 2026-02-10 | $29.99 | 2.4 [E] | 115.4 | 54 [E] | 2 |
| A08 | Blue Prince | small (solo for years, then ~3–5) | 2025-04-10 | $29.99 | 0.7 Steam [E] (2M+ players incl. subscriptions [C]) | 19.2 | 15.8 Steam [E] | 2 |
| A09 | BALL x PIT | 7 (1 lead + 6 remote) | 2025-10-15 | $14.99 | 2 [C] | 35.4 | 22.5 [E] | 4 |
| A10 | RV There Yet? | 4 devs | 2025-10-21 | ~$7.99 | 6 [E] (4.5M+ by Dec 2025 [C]) | 100 | 36 [E] | 3 |
| A11 | YAPYAP | ~10 (remote) | 2026-02-03 | $9.99 | 1.25 [E] | 14.8 | 9.4 [E] | 4 |

### Group B – small viral games (1–5 people)

| ID | Game | Team | Release | Price | Units / players (M) | Peak CCU (k) | Gross (US$M) | AI score |
|---|---|---|---|---|---|---|---|---|
| B01 | **How to Fish** (benchmark) | 2 | 2026-08-20 | $7.99 | ≥6.3 [E] (1M in 2 days [C]) | 374 | ≥26 [E] | 3 |
| B02 | Machine Party | 2 core + composer | 2026-07-30 | $7.99 | 1+ [C] | 22 | 6 [E] | 4 |
| B03 | Sledding Game | 1 | 2026-04-30 (EA) | $7.99 | 0.17 [E] | 3.2 | 0.85 [E] | 4 |
| B04 | Project P.I.T.T. | 1 | 2026-08-19 | $9.99 | 0.07 [E] (50k in 5 days [C]) | 3.9 | 0.5 [E] | 4 |
| B05 | Tangy TD | 1 | 2026-03-09 | $9.99 | 0.1 [E] | 1.2 | 0.9 [E] ($788k in month 1 [C]) | 4 |
| B06 | Agreeee | 1 | 2025-12-05 | $4.99 | 0.05 [E] | 0.6 | 0.19 [E] | 4 |
| B07 | Bongo Cat | 2 | 2025-03-05 (viral May 2025; resurgence Sep 2026) | free | 5.7 players [C] | 193.9 | ~0.1 [E] | 5 |
| B08 | CloverPit | 2 | 2025-09-26 | $9.99 | 1.1 [E] (1M+ [C]) | 25.1 | 8.2 Steam [E] | 5 |
| B09 | Baby Steps | 3 | 2025-09-23 | $19.99 | 0.08 [E] | 1.0 | 1.15 [E] | 3 |
| B10 | Mage Arena | 1 | 2025-07-24 (EA) | $2.99 | 1.8 [E] | 17.4 | 2.6 [E] | 4 |
| B11 | Cast n Chill | 2–4 (unverified) | 2025-06-16 | $14.99 | 0.33 [E] | 4.4 | 3.7 [E] | 5 |
| B12 | Grow a Garden (Roblox) | 1 (original) → ~12 (live-ops) | 2025-03-26 (viral May–Aug 2025) | free | 36.0B visits | 22,346.7 | 250 player spend [E] | 5 |
| B13 | Steal a Brainrot (Roblox) | ~2 (original) + DoBig Studios | 2025-05-16 | free | 73.9B visits | 25,836.2 | 325 player spend [E] | 5 |
| B14 | 99 Nights in the Forest (Roblox) | 3 | 2025-03 | free | 29.9B visits | 14,153.2 | 165 player spend [E] | 4 |
| B15 | Brainrot Puzzle (Poki) | 1 | 2025-05 | free (ads) | 67M plays across 5 games [C] | 17 | 0.2 [E] | 5 |
| B16 | Wplace (web) | 1–3 (unverified) | 2025-07-21 | free | 1M+ users in 4 days | n/a | no data | 4 |
| B17 | Is This Seat Taken? | 2 | 2025-08-07 | $9.99 | 0.3 Steam [E] | 1.7 | 2.4 Steam [E] | 5 |
| B18 | Desktop Defender | 1 (inferred) | 2025-11-04 | $4.99 | 0.09 [E] | 2.7 | 0.33 [E] | 5 |
| B19 | Gamble With Your Friends | ~4 devs | 2026-05-01 | $7.99 | 3.2 [E] (2M in 1 month [C]) | 42.5 | 16 [E] | 4 |
| B20 | Big Walk | 5 | 2026-08-04 | $19.99 | 1+ [C] (6 days) | 46.4 | 21 Steam, Aug [E] | 2 |

Notes:
- **Roblox "gross"** is estimated *player spend*. The creators' net is roughly 25–30% of that.
- **Bongo Cat** launched one month before the window. It is included because of its May 2025 viral peak and its September 2026 resurgence (188.8k concurrent players).

### Group C – context cases (not counted as small teams)

| ID | Game | Why it is here | Key numbers |
|---|---|---|---|
| C01 | BidKing (Steam, $2.99) | A cheap Chinese auction/bluff game. Team size unknown (company credits). | ~57k peak concurrent players; ~0.6M units [E]; reviews fell to **33% positive**; went free-to-play. **Players without quality do not last.** |
| C02 | Meowdoku! (mobile) | Large publisher (Learnings/Oakever) | ~40–45M installs [E]; $13–25M ad revenue [E] against a reported **~$500k/day in paid ads** [E]. Mobile charts are bought. |
| C03 | Smash Fest! (mobile) | Studio of Peak Games veterans, headcount unknown | #1 on the US iOS free chart; ~20–27M installs [E]. **Pulled from Google Play after a copyright claim** over a copied mechanic. |
| C04 | BOMBANANA! (Steam) | "Small independent team", publisher-financed, headcount unknown | **#1 demo of June 2026 Next Fest**: 675k fest players and 6M+ demo players [C]. Developer claims 1M copies in 10 days [C], but trackers say ~110k [E], so this is a conflict. |

**Excluded but useful comparisons** (outside the window, or teams larger than 20):
- *R.E.P.O.* (Feb 2025): ~19M downloads, >$152M [E – AppMagic].
- *Schedule I* (Mar 2025, a solo developer at launch): >10.2M copies, >$189M [E – AppMagic].
- *Windrose* (Apr 2026, ~60-person studio): 1M sales in six days [C], and a reported 2M in its first month.
- *Clair Obscur: Expedition 33* (Sandfall, more than 20 people). Its Indie Game Awards were rescinded over leftover AI placeholder textures [C].

Sources: [AppMagic – friendslop 2025](https://appmagic.rocks/blog/friendslop-steam-games-2025), [Automaton – Windrose team](https://automaton-media.com/en/interviews/open-world-pirate-game-windrose-is-a-souls-lite-survival-adventure-made-by-a-group-of-hardcore-gamers-producer-talks-about-the-games-orig/), [Gematsu – Windrose 1M in six days](https://www.gematsu.com/2026/04/windrose-early-access-sales-top-one-million-in-six-days), [AV Club – Clair Obscur IGA](https://www.avclub.com/clair-obscur-genai-iga-awards-rescinded).

---

## 4. What viral small games have in common

Evidence is drawn from the 31 Group A and B games, with Group C as counter-examples.

### 4.1 Scope

- **One core verb plus one social twist**, for example:
  - *Meccha Chameleon*: paint and hide.
  - *How to Fish*: fish and shoot.
  - *Gamble With Your Friends*: gamble from a shared wallet.
  - *RV There Yet?*: drive and winch.
  - *BOMBANANA!*: communicate despite handicaps.
- **Little content at launch.** One map or biome and 10–30-minute sessions. Content comes later in free updates: *How to Fish* (5 weeks after launch), *PEAK*, *RV There Yet?*, and weekly updates on Roblox.
- **Development time.** The viral co-op hits took **2–12 months**. The craft hits (*Silksong*, *Mewgenics*, *Blue Prince*, *Big Walk*, *Baby Steps*) took **4–8 years**. A long timeline did not make *Baby Steps* or *Tangy TD* bigger than 2-month projects.

### 4.2 Price

- Paid viral games cluster at **$4.99–$9.99**. **$7.99 is the most common list price**, often with a **launch price of $4.95**.
- Cheap prices and friend groups produce very high units per review (80–280) and very high concurrent player counts.
- Premium-priced hits ($15–30) were mostly long-cycle craft games from studios with an established name: Team Cherry, Mega Crit, Edmund McMillen, House House.

### 4.3 Hook design

Every hit passes three tests:
1. **One-sentence pitch.**
2. **A clip-worthy moment within 60 seconds** (failure is funny, success is spectacular).
3. **A reason to bring friends or an audience** (co-op, voice chat, streamer-friendly drama).

Single-player hits replace (3) with **"numbers go up" synergy builds**, which create screenshot and clip moments:
- *Megabonk*
- *BALL x PIT*
- *CloverPit*
- *Slay the Spire 2*

### 4.4 Marketing channels that worked

| Channel | Examples |
|---|---|
| Developer devlogs on TikTok/YouTube/Instagram before launch | *How to Fish* (weekly, several million views), *Sledding Game* (millions of views), *Megabonk* (dev YouTube channel) |
| A free version or demo that big YouTubers pick up | *Project P.I.T.T.* (itch.io → 10M+ YouTube views → 115k wishlists) |
| A free game built on a well-known meme | *Bongo Cat* (huge reach, tiny revenue; see 4.5) |
| Steam Next Fest demo | *BOMBANANA!* (#1 demo), *YAPYAP*, *Desktop Defender* (from ~3 to 1,500 demo concurrents, +20k wishlists), *BALL x PIT*, *CloverPit* |
| The developer's own streaming audience | *Tangy TD* (Twitch), *Agreeee* (spread by VTubers) |
| Streamer group play after launch | *How to Fish* (TheBurntPeanut), *R.E.P.O.*, *PEAK*, *Mage Arena*, *Gamble With Your Friends* |
| Label or network halo | Landfall/Evil Landfall (*How to Fish*, *PEAK*), Devolver (*BALL x PIT*, *Baby Steps*), Panic (*Big Walk*), the TENSTACK collective (*Gamble With Your Friends*, bundled with *Sledding Game*) |
| Platform featuring | Nintendo Indie World shadow-drop (*Is This Seat Taken?*, *Blue Prince* on Switch 2), day-one Game Pass (*Sledding Game*, *BALL x PIT*, *Blue Prince*) |
| Roblox algorithm + TikTok + weekly updates | *Grow a Garden* (weekly Saturday updates; joined by Splitting Point at ~500–1,000 concurrent players, reached 1M within about a month [C]) |
| Riding a meme at its peak | *Brainrot Puzzle* (1M plays in a day), *Steal a Brainrot* |

**A notable cluster: Swedish friendslop.**
- *How to Fish*, *RV There Yet?*, *Gamble With Your Friends* (TENSTACK) and Landfall's *PEAK* (with Aggro Crab) all come from a small, connected Swedish scene.
- *R.E.P.O.* is Swedish too.
- These studios cross-promote with **bundles** and investment.

Joining a network like this (a publisher-light label, a collective, a bundle partner) is a realistic lever for a solo developer.

### 4.5 Counter-evidence

- **Streamer buzz does not equal sales.** *Baby Steps* was everywhere on streams but sold an estimated ~50–100k on Steam. Watching it was the entertainment.
- **Reach does not equal revenue.** *Bongo Cat* had ~194k concurrent players and 5.7M players but made about $3k/month net in 2025 [C]. About half of its concurrent players were bots farming tradable item drops [E]. **Free plus tradable drops is a bad model.**
- **A spike does not equal quality.** *BidKing* reached ~57k concurrent players and then fell to 33% positive reviews.
- **Mobile charts are bought.** The two mobile chart-toppers we examined are both publisher-scale games: one funded by paid ads (*Meowdoku!*), and one from a studio of industry veterans whose headcount is unknown (*Smash Fest!*). Neither is a solo or tiny-team viral hit. *Smash Fest!* was also removed from Google Play over a copied mechanic.
- **Hits fade fast.** *Meccha Chameleon* fell from a 340k peak to about 22k daily players two months later. Plan updates, a sequel or a next game; do not plan on a single title being a pension.

---

## 5. TOP 5 opportunities for a solo developer with AI

### 5.1 How the top 5 were chosen

I scored candidate games on:
- **earning potential (P)**, from what comparable small teams actually earned;
- **AI feasibility / ease (F)**, the 1–5 score in the data;
- **market risk (R)**, where 5 means the lowest risk, judged from competition, how hit-driven the format is, and platform base rates.

| Template game(s) | Team that made it | Earned (gross) | P | F | R | P×F | Verdict |
|---|---|---|---|---|---|---|---|
| CloverPit | 2 | ~$8M Steam + Game Pass/mobile/console [E] | 4 | 5 | 3 | 20 | **#1** |
| Meccha Chameleon / How to Fish / Gamble With Your Friends | 2 / 2 / ~4 | $66M / ≥$26M / $16M [E] | 5 | 4 (3 for How to Fish) | 2 | 20 | **#2** |
| Megabonk (+ BALL x PIT) | 1 (7) | ~$40M ($22.5M) [E] | 5 | 4 | 2 | 20 | **#3** |
| Cast n Chill / Desktop Defender / Bongo Cat | 2–4 / 1 / 2 | $3.7M / $0.33M / ~$0.1M [E] | 3 | 5 | 4 | 15 | **#4** (lowest risk) |
| Grow a Garden / 99 Nights / Steal a Brainrot | 1 / 3 / ~2 | $165–325M player spend [E] | 5 | 5 | 1 | 25 | **#5**. Highest nominal score, but the most extreme lottery: median DevEx creator ≈ $1.5k/year |
| Is This Seat Taken? | 2 | ~$2.4M Steam [E] | 3 | 5 | 3 | 15 | Runner-up (needs strong puzzle-design skill) |
| Mage Arena | 1 | ~$2.6M [E] | 3 | 4 | 2 | 12 | Folded into #2 |
| Project P.I.T.T. / Sledding Game / Tangy TD | 1 each | $0.5M / $0.85M / $0.9M [E] | 2 | 4 | 3 | 8 | Good first-game outcomes, smaller ceiling |
| Brainrot Puzzle (web) | 1 | ~$0.2M [E] | 1 | 5 | 3 | 5 | Fast practice, not a business on its own |

All ideas below are **original concepts inspired by** the templates, not copies. Before committing to any of them, search Steam and Roblox for name and concept collisions.

**Default toolset (shared by all five)**

| Need | Tools | Approximate cost (2026) |
|---|---|---|
| Code | **Claude Code** (Pro $20 or Max $100–200/month) plus an engine MCP server (e.g. the free open-source *godot-mcp*) so Claude can run scenes and read errors | Pro $20 or Max $100–200/month |
| 2D / pixel art | PixelLab, or the Retro Diffusion Aseprite extension, or Midjourney/Scenario; clean up in Aseprite or Krita | PixelLab ~$12–50/month; Retro Diffusion $20–65 one-time |
| 3D models | Meshy (Pro ~$20/month) or Tripo (~$20/month), plus Blender for cleanup and retopology; free CC0 packs from Kenney | Pro tiers ~$20/month |
| Sound and music | ElevenLabs sound effects; Suno Pro (paid plans include commercial rights) | Suno Pro $10/month |
| Video for TikTok / Shorts | OBS + CapCut | free |
| Store fees | Steam Direct; Apple; Google | $100 per game; $99/year; $25 once |

AI art policy:
- **Steam requires disclosure of AI content that players see.** Coding assistants have been exempt since January 2026.
- Because roughly a quarter of US players react negatively to AI art, keep the **capsule and key art human-made** (commission $200–800) and hand-edit visible AI assets.

---

### #1 – "One More Cast": a push-your-luck fishing roguelite (single-player)

**Template:** *CloverPit* (2 developers, 1M+ copies, ~$8M on Steam [E], AI score 5), plus the *Balatro*/*Luck be a Landlord* lineage. It borrows the fishing theme from *How to Fish*, without the netcode.

**Why it's a good candidate:**
- Single-player and essentially one screen.
- All depth comes from **data-driven item synergies**, which is the kind of code AI writes well and quickly.
- "Numbers explode" moments make clips.
- Proven appetite for gambling-flavoured roguelites at $5–10. *CloverPit* later added Game Pass, mobile and console income.
- Low art load: one pier scene and about 60 icons.

**Original concept:**
- **Setup:** you owe the cannery boss. Each day you get 5 casts.
- **The cast (push your luck):** a cast draws creatures one by one from your "lake bag". Each pull adds value and a multiplier. Pull again, or cut the line and bank the catch. Hooking a Snapper (which takes 2 strikes) or a Shark ends the cast with nothing.
- **Building the bag:** **bait** adds creatures to the bag; **lures** (relics) rewrite the rules. Examples: "eels next to crabs double", "every third pull is safe", "sharks become mega-fish if you own a harpoon".
- **Pressure:** quotas rise every 3 days. Missing one means the boss sinks your boat.
- **Meta-progression:** new lakes (Swamp, Arctic, Abyss) and new lures.
- **Runs:** 20–40 minutes.
- **Hook sentence:** *"Blackjack with fish: every cast you decide whether one more pull is worth losing everything."*

**MVP plan (3 weeks):**
- **Week 1 – rules engine.**
  - Godot 4 plus Claude Code.
  - Data-driven creatures and lures (Godot Resources or JSON); the bag/draw/bust logic; scoring; the day and quota cycle.
  - 20 creatures and 15 lures.
  - Unit tests for the scoring rules (ask Claude to write them).
  - Placeholder UI.
- **Week 2 – feel and art.**
  - One pier scene (AI concept, then paint-over); creature icons (PixelLab/Retro Diffusion, cleaned in Aseprite).
  - Juice: tension sound rising with each pull, a screen shake on bust, number pop-ups.
  - Shop between days; 40 lures in total.
  - SFX (ElevenLabs) and one music loop (Suno).
- **Week 3 – balance and test.**
  - Run logging to CSV (seed, picks, score).
  - 10–20 outside testers (itch.io page and a Discord).
  - Tune quotas until roughly 30% of runs win.
  - Record 10 short clips of big combos; make a Steam page with a commissioned capsule.
- **Then:** demo in the next Steam Next Fest, and weekly TikTok/Shorts of absurd combos.

**Platform and monetization:**
- Steam premium **$4.99–6.99** with a launch discount; a free demo.
- Later: Switch through a porting partner, and a mobile premium version (*CloverPit*'s path).
- No ads and no in-app purchases in the PC version.
- **Polished version:** 3–5 months, $1.5k–5k (tools, commissioned capsule, optional freelance music).

---

### #2 – "Pigeon Heist": a 2–4 player online co-op party game (the How to Fish recipe, scoped for one person)

**Templates:** *Meccha Chameleon* (2 developers, ~2 months, 20M copies [C]), *How to Fish* (2 developers, 12 months), *Gamble With Your Friends* (~4 developers, 2M in a month [C]), *RV There Yet?* (4 developers, ~2 months).

**Why it's a good candidate:**
- The highest ceiling in the whole dataset, and the format Steam's audience is currently buying.
- Two-person teams proved it can be built quickly.
- Most of the networking boilerplate (Steam lobbies, P2P sync) is well documented, which makes it AI-friendly.
- Difficulty is **3–4/5**. Keep it manageable by using **few networked physics objects**, a host-authoritative design, and no dedicated servers.

**Original concept:**
- **Setup:** 2–4 players are city pigeons robbing a busy park.
- **Teamwork:** small snacks are carried alone; **big loot needs teamwork** (a baguette takes 2 pigeons, a wedding cake takes 4, all flapping in sync).
- **Opponent:** the park keeper patrols with a broom; a hit means a ragdoll pigeon. Distract him with coos, decoys, or a well-timed "aerial delivery" that makes him slip.
- **Progression:** sell loot to the Pigeon Don to unlock new locations (street market, wedding, stadium hot-dog stand) and silly hats.
- **Rounds:** 8 minutes.
- **Hook sentence:** *"Four pigeons, one wedding cake, one very angry park keeper."* Cute animals plus physics comedy produce a clip every round.

**MVP plan (4 weeks):**
- **Week 1 – networking first, because it is the riskiest part.** Unity 6 + Facepunch.Steamworks + Netcode for GameObjects (or Godot 4 + GodotSteam).
  - Create and join lobbies through Steam invites.
  - 4 pigeons walk, flap and glide in sync.
  - One "carryable" object with up to 4 holders.
  - **Test over the internet with a friend by day 5.** If sync feels bad, simplify the physics now. Claude Code can generate the networking code; you supply the testing.
- **Week 2 – core loop.**
  - One park map (Kenney/Synty-style packs plus Meshy props).
  - The keeper AI: patrol → notice → chase → swat.
  - Loot weights; a nest drop-off for scoring; round timer; results screen with "best fail".
- **Week 3 – comedy and feel.**
  - Ragdolls; coo and honk emotes (ElevenLabs).
  - A slip mechanic for the keeper; round modifiers (rain, a picnic festival).
  - Hats bought with loot money.
- **Week 4 – group playtests.**
  - At least 3 groups of 4 people; fix desyncs.
  - Cut 30-second clips from playtests for TikTok.
  - Steam page plus a Steam Playtest sign-up.
  - Start **weekly devlog posts**, the *How to Fish* playbook.

**Platform and monetization:**
- Steam premium **$5.99–7.99**, with a launch discount to about $4.95 and a 4-pack bundle.
- Free content updates; optional cosmetic DLC later.
- Pitch to friendslop-friendly labels or investors (Evil Landfall-style project investment, collectives like TENSTACK) for bundles and halo.
- **Polished version:** 6–9 months, $3k–12k.

---

### #3 – "Mower Mayhem": a 3D survivors-like where your movement is your weapon

**Template:** *Megabonk* (solo, ~$40M [E], Unity, low-poly, about 12 months), plus *BALL x PIT* ($22.5M [E]). Single-player, so there is no netcode.

**Why it's a good candidate:**
- A solo developer proved the ceiling.
- Low-poly assets are easy to generate or buy.
- Upgrades are data-driven.
- Absurd build scaling makes clips.

**Risk:** the genre is crowded. The differentiator must be visible in a single GIF.

**Original concept:**
- You ride a lawnmower through a suburb overrun by evil garden gnomes.
- **Speed and drift deal the damage**: there is no auto-attack until you bolt on upgrades.
- Bolt-ons: sprinklers, leaf blowers, a firework launcher, a trailer of angry geese.
- Gnomes ragdoll and fly; combos chain the knockback.
- Bosses: a giant plastic flamingo and a sentient hedge.
- **Hook sentence:** *"Vampire Survivors, but you're a lawnmower and physics is the damage."*

**MVP plan (3–4 weeks):**
- **Week 1:** vehicle controller (drift, boost); horde spawner with object pooling and GPU instancing so 500+ enemies run smoothly (ask Claude for Godot MultiMesh or Unity instancing); speed-based collision damage; XP pickups; level-up choice UI.
- **Week 2:** 12 attachments and 6 passives with synergy rules; 3 enemy types, 1 elite and 1 boss; one suburb map; a 15-minute run.
- **Week 3:** juice (gnome yeet physics, damage numbers, screen shake); audio; meta-unlocks.
- **Week 4:** performance pass on Steam Deck–class hardware, external playtests, a demo build.

**Platform and monetization:** Steam premium **$4.99–7.99**, a free demo for Next Fest, Steam Deck Verified. Later, consoles through a publisher or porting partner. **Polished version:** 4–7 months, $2k–6k.

---

### #4 – "Koi Desk": a desktop-companion idle game (lowest risk, fastest path to a first sale)

**Templates:**
- *Cast n Chill*: idle pixel fishing in a corner of the screen; ~$3.7M [E] at $14.99; launched during Steam's Fishing Fest.
- *Desktop Defender*: solo; Next Fest demo jumped from ~3 to 1,500 concurrents.
- *Bongo Cat*: ~194k concurrent players, which proves demand, but it is free with tradable drops, which failed commercially.

**Why it's a good candidate:**
- AI score 5 and a tiny scope.
- People leave these games running for hours, which pushes them up Steam's "most played" charts.
- Cozy, streamer-friendly (a pond in the corner of a stream), and it fits your fishing interest.

**Lessons applied:**
- Charge a **premium price**.
- **No tradable item drops**: avoid *Bongo Cat*'s bot problem.

**Original concept:**
- A small koi pond lives at the bottom edge of your screen.
- Your activity "rains" food pellets. It only counts activity; it never records keys.
- Koi grow and **breed with inheritable pattern genes** (a light *Mewgenics*-style genetics meta), so you chase rare patterns and fill a collection book.
- Sell koi for coins and buy lanterns, lilies and a tiny bridge.
- Seasonal events: cherry blossom, snow.
- **Hook sentence:** *"Breed rare koi while you work."*

**MVP plan (2–3 weeks):**
- **Week 1:** Godot 4 transparent, borderless, always-on-top window anchored to the taskbar, with click-through outside the pond. Activity counter using idle time and input counts, with a clear privacy statement. 3 koi; feeding and growth; save and load.
- **Week 2:** genetics (2–3 pattern genes and 20 visible patterns); breeding; collection book; decoration shop; pixel art (PixelLab plus manual cleanup); lo-fi music (Suno); settings (size, position, mute, streamer mode).
- **Week 3:** polish; a Steam page with GIFs of the pond on a real desktop; a demo for Next Fest; short TikToks ("my koi bred a golden one during a meeting").

**Platform and monetization:** Steam premium **$3.99–4.99**. Later: a cosmetic pond-theme DLC and a soundtrack DLC. Optional mobile companion app. **Polished version:** 2–4 months, $800–3k.

---

### #5 – "Raise a Reef": a Roblox collection simulator (cheapest to test, most lottery-like)

**Templates:**
- *Grow a Garden*: original built in about 3 days by a teenager; 22.3M peak concurrent players [C].
- *99 Nights in the Forest*: built as a one-week project by 3 founders; 14.2M peak [E].
- *Steal a Brainrot*: 25.8M peak [E].

**Why it's a good candidate:**
- AI writes Luau well.
- Roblox Studio is free, and there is no store fee up front.
- You can ship in 1–2 weeks and learn from real players immediately.
- The upside is enormous.

**But the base rate is brutal.** The median DevEx creator earned about **$1,500** in the 12 months to June 2026, while the top 10 averaged $65.7M [C]. Copycats appear within days. The audience is young, so monetization must be fair.

**Original concept:**
- **Grow:** plant coral seeds on your reef plot. They grow in real time, even offline.
- **Attract:** coral combinations attract fish of different rarities.
- **Mutate:** global ocean events every 20 minutes mutate fish (Storm, Bioluminescent Night, Red Tide, Whale Migration).
- **Earn:** fish sell for shells.
- **Socialise:** visit and trade with other players; a "night-diver" mechanic lets players sneak-net fish from unguarded reefs (light *Steal a Brainrot* tension); weekly new species.
- **Hook sentence:** *"Grow a reef; whatever swims in is yours."*

**MVP plan (2 weeks):**
- **Week 1:**
  - Roblox Studio + **Rojo**, so Claude Code edits Luau files in a normal folder.
  - Plot assignment; seed shop; real-time growth stored with DataStores; fish spawning by coral combos.
  - Sell loop; leaderboards.
- **Week 2:**
  - Ocean events with mutations; trading or visiting.
  - **Game passes** (2× growth, extra plot, auto-sell) and **developer products** (instant grow, event bait).
  - Daily rewards; icon and thumbnails (human-touched).
  - Launch with a small Roblox ads test ($50–200).
- **Then:** an update every Saturday (*Grow a Garden*'s cadence), and TikToks of rare mutations.

**Platform and monetization:**
- Roblox: game passes, developer products and Premium Payouts, cashed out through DevEx.
- Creators keep about 70% of Robux spent; DevEx is about $0.0038 per Robux, so roughly 25–30% of player spend reaches the creator. That share rose to 37.8% for age-verified US 18+ spend in qualifying experiences from June 2026, per press reports.
- **Polished / live-ops version:** ongoing. Budget 1–2 days of work per week, indefinitely.

---

## 6. Risks and realistic expectations

### 6.1 Income distribution (base rates)

**Steam:**
- Releases: about 19,000 in 2024, **20,282** in 2025, and **20,220 already by 1 Oct 2026** (on track for a record 24–27k) [E – SteamDB/VG Insights/Tom's Hardware].
- **Median gross for a 2025 release: ~$249.**
  - ~66% grossed under $1,000 and ~40% under $100 (less than the $100 Steam fee).
  - ~8% passed $100k.
  - **0.5–1.5% passed $1M** (roughly 95–300 games).

  [E – Ziva citing VG Insights/Alinea; Gamalytic; Alinea]
- **Only 608 of 20,282 (2.99%)** 2025 releases reached 1,000 reviews. About half have fewer than 10 [E – How To Market A Game / SteamDB].
- Valve says **5,863 titles** (from all years) earned over $100k on Steam in 2025 [C – Valve, GDC 2026].
- Indie games took ~25% of Steam's 2025 revenue ($4.4–4.5B of ~$17.7B). The **top 5 new indies alone took over $500M** [E – Alinea]. In September 2026, new IP took only ~20% of top-500 revenue [E].
- **Wishlists to sales:** first-week sales ≈ **0.10–0.15× launch wishlists**, and year 1 ≈ 2.5× week 1 [E – GameDiscoverCo]. Example: 20k wishlists → ~2–3k first-week copies → ~5–8k in year one → about $25–50k gross at $7.99.

**Roblox:**
- Top 10 creators averaged **$65.7M**; the **median DevEx creator earned ~$1,500** (12 months to June 2026, ~$1.7B paid in total) [C – Roblox RDC 2026 via press].
- Roughly 100–250 accounts earned $1M or more [E].

**Browser portals:** about **$0.5–4 per 1,000 plays** to the developer [E], so 1M plays ≈ $500–4,000. Poki says its top developers earn $50k–$1M a year [C].

**Mobile:** paid user acquisition keeps getting more expensive. Hybrid-casual Android cost per install went from $0.54 to $0.95 in a year; US casual iOS installs cost $2–4 [E]. A solo developer cannot out-buy the publishers who dominate the charts (see Group C).

Sources: [Ziva – indie revenue](https://ziva.sh/blogs/indie-game-revenue); [MP1st – 40% under $100](https://mp1st.com/news/40-of-steam-games-in-2025-earned-less-than-100); [How To Market A Game – what happened in 2025](https://howtomarketagame.com/2026/01/27/what-the-hell-happened-in-2025/); [Game Developer – Valve 5,863 titles](https://www.gamedeveloper.com/business/valve-says-5-836-titles-earned-over-100-000-on-steam-in-2025); [Notebookcheck – indie 25% of Steam revenue](https://www.notebookcheck.net/Indie-games-accounted-for-25-of-Steam-s-revenue-in-2025.1189429.0.html); [GameDiscoverCo – wishlist conversions](https://newsletter.gamediscover.co/p/the-state-of-steam-wishlist-conversions); [Dexerto – Roblox creator earnings](https://www.dexerto.com/roblox/robloxs-top-creators-average-65-7-million-a-year-but-most-make-far-less-3408675/); [How To Market A Game – is friendslop saturated?](https://howtomarketagame.com/2026/07/30/is-friendslop-saturated/). Full citations are in `data/_market_stats.md`.

### 6.2 What separates hits from the rest

1. **A hook you can explain in one sentence, and a clip within a minute.** Every Group A/B hit passes this. Most of the 20k yearly releases do not.
2. **A social engine.** Friends recruit friends (the 4-pack effect), or the game is built for streamers. Without one, a game needs top-tier craft (*Silksong*, *Blue Prince*) or a "numbers go up" loop (*Megabonk*, *CloverPit*).
3. **Price.** At or below $10 with a launch discount, unless you have a brand.
4. **An audience before launch.** Devlogs, a demo or Next Fest, a Discord, and 10k–100k+ wishlists. Exceptions such as *PEAK* and *Meccha Chameleon* had a label halo or a hook so strong it went viral within days.
5. **Quality of feel.** The hits mostly sit at 84–97% positive reviews. *BidKing* (33%) shows that a spike without quality collapses.
6. **Speed and iteration.** Small scope, shipped fast, updated quickly while attention lasts.
7. **Timing.** *Megabonk*, *CloverPit* and *Baby Steps* all moved their launch dates to avoid *Silksong*.
8. **Multiple shots.** Dazed Games' first commercial game failed before *How to Fish*. Kenny Sun, vedinad, Mike Klubnika and House House all had earlier games. The *Tangy TD* developer streamed development for four years.

### 6.3 AI-specific risks

- **Disclosure.** Steam requires you to disclose AI content that players see (art, audio, text, marketing). Coding assistants have been exempt since January 2026 [C]. About 31% of 2026 releases disclose AI, but those games take only ~10–27% of sales [E].
- **Player sentiment.**
  - Only ~8% of engaged Steam users reject AI games outright [E – GameDiscoverCo survey].
  - About 25% of US players are less likely to buy [E – Circana].
  - Backlash targets *visible* AI art and cutscenes: *Clair Obscur* lost its Indie Game Awards; *Crimson Desert* apologised for an undisclosed AI painting.
  - Even human-made games get falsely accused of being "AI slop".
- **Mitigation.**
  - Use AI heavily for code, prototyping, sound effects and placeholders.
  - Keep the capsule, key art, characters and trailer human-made or heavily human-edited.
  - Disclose honestly.
  - Avoid live-generated AI content in-game unless you can moderate it.

### 6.4 IP, legal and copycat risks

- **Memes are not free IP.** *Steal a Brainrot*'s Tung Tung Tung Sahur character was pulled in a licensing dispute, and *Bongo Cat*'s rights to the original meme art were publicly questioned.
- **Copying mechanics can get you delisted.** *Smash Fest!* was removed from Google Play after a copyright claim.
- **Fast followers.** A viral hook is cloned within days, especially on Roblox and mobile. Your defence is update speed and community, not secrecy.
- **Trademark and name collisions.** Check Steam and Roblox before choosing a title.

### 6.5 Realistic plan and expectations for you

- **Plan for 3–5 small shots over 12–18 months, not one big game.** Each shot is an MVP in 2–6 weeks, a free demo or itch.io build, and a wishlist test. Kill or continue based on data. A useful bar for continuing: a demo that keeps players for more than 20 minutes and a Steam page gaining 50+ wishlists a day after you start posting.
- **Order the work to learn the pipeline cheaply:**
  1. #4 (desktop idle) or #1 (single-player roguelite) first.
  2. #2 (co-op) once you can ship.
  3. #5 (Roblox) as a parallel experiment if you enjoy weekly live-ops.
- **Expected outcomes for a first commercial Steam game:**
  - **median:** less than $1k;
  - **a good result:** $10k–100k;
  - **a hit:** $1M+ (about 0.5–1.5% of releases).

  The small-team games in this report are the survivors of a very large field; they are not typical outcomes.
- **Budget for each shot:** $150–900 in tools for an MVP, plus $200–800 for a human-made capsule. Your own time is the real cost.

---

## 7. Methodology and limitations

- **How the data was collected.** Nine parallel research agents investigated about 5 games each, then I cross-checked the key figures:
  - *Meccha Chameleon*'s 20M was re-confirmed.
  - The 608 / 20,282 review statistic was re-confirmed.
  - *How to Fish*'s August GameDiscoverCo figures were re-confirmed.
  - *How to Fish*'s September figures could **not** be re-found, so this report uses the August numbers as a floor.
  - *PEAK*'s cost and *RV There Yet?*'s build time rest on single articles listed in the sources.
- **Network limitation.** This environment's network policy blocked direct page fetches (Steam, SteamDB, Gamalytic, Wikipedia). Numbers come from web-search results that cite those pages. Each figure is labelled, dated and sourced, but some tracker snapshots could not be opened to check their exact dates.
- **Estimation methods** (full rules in `research_spec.md`):
  - **Boxleiter:** reviews × 30–60 by default, calibrated against confirmed units where possible. Cheap viral co-op needs 80–280.
  - **Gross:** units × ~0.75 × list price, unless a tracker or GameDiscoverCo figure exists.
  - **Net:** gross × (1 − store cut) × 0.93 for refunds. Steam's tiered cut is 30% up to $10M, 25% to $50M and 20% above.
  - **Roblox net:** about 25–30% of player spend.
  - **Production cost:** people × months × $3–6k per month (an opportunity cost when a developer worked unpaid).
- **Tracker disagreement is large.** For example, Raijin undercounted *YAPYAP*, *RV There Yet?*, *Project P.I.T.T.*, *Tangy TD* and *Megabonk* compared with confirmed developer figures. The spreadsheet's "Data conflicts" column records every disagreement and the value I chose.
- **Group C** keeps popular games that failed or could not pass the 1–5 person test, so the small-team conclusions are not inflated.
