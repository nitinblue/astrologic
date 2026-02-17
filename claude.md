# CLAUDE.md
# Project: AstroLogic / Trading CoTrader
# Last Updated: February 17, 2026 (session 23 — Enriched Interpretation Layer, 3 Variants)
# Historical reference: CLAUDE_ARCHIVE.md (architecture decisions, session log, file structure, tech stack)

## STANDING INSTRUCTIONS
- **ALWAYS update CLAUDE.md** after major changes — update: code map, "what user can do", blockers, open questions.
- **ALWAYS update MEMORY.md** (`~/.claude/projects/.../memory/MEMORY.md`) with session summary.
- **Append new architecture decisions to CLAUDE_ARCHIVE.md**, not here.
- **If context is running low** prioritize writing updates BEFORE doing more work.

---

## [NITIN OWNS] WHY THIS EXISTS
Nitin wants to learn Astrology, starting from all the foundational concepts like sunsign, moon sign, rising sign, planet house, dasha, lagna and the interplay around this
Nitin is looking to build a application, that can be used for daily Astrology todo, to avoids. (no major predictions, nothing). Based on kundali of user.

The agent is a **Vedic Life Coach** — not a fortune teller. It understands the personality framework from your chart and gives grounded, empathetic guidance for everyday things: career, relationships, health, investment, real estate, spirituality, children, workplace.

ONe main application is in Finance. Where i am looking to give some indication on market mood, volatility, price movement of major metals like GOld, Silver, Crude etc. And major indexes
I want to plugin in this service in my other trading application where at tthe start of session i look at market macros, Astro probability weighted direction prediction.

Given date , time and place of birth i want to be able to tell the sunsign moon sign and etc. Already implemented in main.


---

## [NITIN OWNS] BUSINESS OBJECTIVES — CURRENT
<!-- Add new entries at TOP with date. Move completed sessions to CLAUDE_ARCHIVE.md. -->
Study current structure of project and database..
Give me a good .MD file on vedic Astrology


### Feb 15, 2026 (Session 4) — Portfolio Evaluation + Liquidity

| # | Objective | Status |
|---|-----------|--------|
| 1 | . | |


### Standing objectives (from Feb 14-15)
- Always read claude.md at start and update progress etc after every major development


---

## [NITIN OWNS] SESSION MANDATE
<!-- Current session only. Move prior to CLAUDE_ARCHIVE.md. -->

### Feb 17, 2026 (Session 23)
Enrich interpretation layer: 3 text variants per rule, deep grounded text, variant rotation via RL

---

## [NITIN OWNS] TODAY'S SURGICAL TASK
<!-- OVERWRITE each session. 5 lines max. -->
Enriched all interpretation tables with 3 text variants (direct/psychological/coaching).
Fixed variant rotation: random when no ratings, RL-guided after feedback.
Deleted test persons (Rahul, Test Person) from DB.


## [CLAUDE OWNS] WHAT USER CAN DO TODAY

### Vedic Life Coach (Interpretation Engine) — NEW
- Run: `python -m kundali_engine.agent.cli`
- Ask open-ended life questions: "what are my strengths?", "how does AI impact me?", "tell me about my career"
- Special commands: "who am I?" (personality profile), "what is the universe telling me?" (holistic reading)
- Covers 40 life themes: career, job security, relationships, marriage, health, mental health, investment, wealth, real estate, spirituality, education, technology/AI, creativity, children, foreign travel, leadership, business, family, life purpose, and more
- Personalized to your chart: planet houses, dignities, Rahu/Ketu axis, current dasha
- Rate responses: "rate 4" or "5 stars" — drives RL-based text variant selection over time
- Event sourcing: every interaction logged immutably for continuity and learning
- 14 intents: greeting, help, create_chart, show_chart, list_people, dasha_info, today_guidance, trading_regime, sector_advice, planet_info, switch_person, compare, **interpret**, **rate**

### Code Map — Agent Layer
| File | Purpose |
|------|---------|
| `kundali_engine/agent/agent.py` | Core: intent detection (14 intents), routing, session, flow management |
| `kundali_engine/agent/handlers.py` | All handler functions inc. handle_interpret + handle_rate |
| `kundali_engine/agent/interpreter.py` | ChartInterpreter: theme detection, chart reading, rule assembly, RL variant selection, response composition, chart_summary() |
| `kundali_engine/agent/event_store.py` | Event sourcing: log_event, log_feedback, get_variant_scores |
| `kundali_engine/agent/cities.py` | 70+ city → (lat, lon, tz) lookup |
| `kundali_engine/agent/cli.py` | CLI REPL transport |
| `kundali_engine/agent/__init__.py` | Package |

### Database v2 — 39 tables
- `astro_v2.db` is the active database (39 tables, 19 indexes)
- 19 reference tables seeded (15 original + 4 interpretation)
- Interpretation tables (enriched with 3 variants each):
  - ref_life_theme: 40 rows (themes, no variants)
  - ref_rahu_ketu_axis: 36 rows (12 axes × 3 variants, composite PK)
  - ref_planet_house_meaning: 324 rows (108 combos × 3 variants)
  - ref_planet_theme_meaning: 138 rows (46 combos × 3 variants)
- Variant angles: V1=Direct/practical, V2=Psychological/relational, V3=Growth/coaching
- Event tables: event_log (append-only), event_feedback (ratings for RL)
- Persons: Nitin, Priyanka, Vainavi, Anushka (Rahul + Test deleted)

### Code Map — Database Layer
| File | Purpose |
|------|---------|
| `kundali_engine/core/database/schema_v2.sql` | 39-table schema (ref, natal, transit, output, entity, interpretation, events) |
| `kundali_engine/core/database/schema_v1.sql` | Old 4-table schema (backup) |
| `kundali_engine/core/database/seed_reference_data.py` | Seeds 15 ref_ tables (idempotent) |
| `kundali_engine/core/database/seed_interpretation_data.py` | Seeds 4 interpretation ref_ tables (40 themes, 12 axes, 108+46 meanings) |
| `kundali_engine/core/database/migrate_v1.py` | One-time v1→v2 data migration |
| `kundali_engine/core/database/init_db.py` | Creates v2 schema + seeds all ref + interpretation tables |
| `kundali_engine/core/database/connection.py` | `astro_v2.db`, FK ON |

### What's Ready to Build Next
- Move cities from dict to ref_city DB table
- Full dasha hierarchy computation (currently only maha-level in DB)
- Transit position feed (daily ephemeris → transit_position table)
- Transit-based daily guidance (combine static personality + dynamic transits)
- Ashtakavarga computation (BAV/SAV tables ready)
- Entity charts (company/index natal data)
- Refactor create_kundali.py constants to read from ref_ tables (DRY)
