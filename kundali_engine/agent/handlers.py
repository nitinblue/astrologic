"""
Handler functions for each agent intent.

Every handler has the signature:  handle_xxx(message, session) -> str
They return plain text suitable for CLI, WhatsApp, or web.
"""

import re
from datetime import datetime, date

from kundali_engine.core.database.connection import get_connection, DB_PATH
from kundali_engine.agent.cities import lookup_city, CITIES
from kundali_engine.agent import event_store

# ── Help text (reused in greeting + unknown intent) ─────────────────────────

HELP_TEXT = """\
Here's what I can do:

  Life questions  - "what are my strengths?" "how does AI impact me?"
                    "tell me about my career" "what is the universe telling me?"
  Personality     - "who am I?" "my personality" "my weaknesses"
  Create a chart  - "create kundali for [name] born [date] [time] [place]"
  Show a chart    - "show my chart" or "show Priyanka's chart"
  List people     - "who all do you have?"
  Current dasha   - "what dasha am I in?"
  Daily guidance  - "how's today?"
  Trading regime  - "should I trade today?"
  Sector advice   - "which sectors are good?" or "should I buy gold?"
  Planet info     - "tell me about Saturn"
  Switch person   - "switch to Priyanka"
  Compare charts  - "compare me with Priyanka"
  Rate a response - "rate 4" or "5 stars" (helps me learn)

Type 'cancel' during any multi-step flow to abort."""


# ═════════════════════════════════════════════════════════════════════════════
# GREETING / HELP
# ═════════════════════════════════════════════════════════════════════════════

def handle_greeting(message, session):
    name = _get_active_person_name(session)
    greeting = f"Namaste{' ' + name if name else ''}!"
    return f"{greeting} I'm your Vedic astrology guide.\n\n{HELP_TEXT}"


def handle_help(message, session):
    return HELP_TEXT


# ═════════════════════════════════════════════════════════════════════════════
# CREATE CHART  (inline or multi-step conversational flow)
# ═════════════════════════════════════════════════════════════════════════════

def handle_create_chart(message, session):
    """Try to parse all fields inline; fall back to conversational flow."""
    parsed = _try_parse_inline_chart(message)

    if parsed and all(k in parsed for k in ("name", "dob", "tob", "place")):
        return _execute_create_chart(parsed, session)

    # Start conversational flow with whatever we parsed so far
    session["flow"] = "create_chart"
    session["flow_data"] = parsed or {}
    return _ask_next_create_field(session)


def continue_create_chart_flow(message, session):
    """Handle each step of the multi-step chart creation."""
    data = session["flow_data"]
    step = data.get("_step", "name")

    if step == "name":
        data["name"] = message.strip().title()
        data["_step"] = "dob"
        return "Date of birth? (e.g. 15 Jun 1990 or 1990-06-15)"

    if step == "dob":
        dob = _parse_date(message.strip())
        if not dob:
            return "Couldn't parse that date. Try: 15 Jun 1990, 1990-06-15, or 15/06/1990"
        data["dob"] = dob
        data["_step"] = "tob"
        return "Time of birth? (e.g. 14:30 or 2:30 PM)"

    if step == "tob":
        tob = _parse_time(message.strip())
        if not tob:
            return "Couldn't parse that time. Try: 14:30, 2:30 PM, or 6:10am"
        data["tob"] = tob
        data["_step"] = "place"
        return "Place of birth? (e.g. Delhi, Mumbai, Ranchi)"

    if step == "place":
        place = message.strip()
        city = lookup_city(place)
        if not city:
            data["place"] = place
            data["_step"] = "coords"
            return (
                f"I don't have coordinates for '{place}' in my city list.\n"
                "Please provide latitude and longitude (e.g. 28.61, 77.20)"
            )
        lat, lon, tz = city
        data["place"] = place.title()
        data["lat"] = lat
        data["lon"] = lon
        data["tz"] = tz
        session["flow"] = None
        return _execute_create_chart(data, session)

    if step == "coords":
        coords = _parse_coords(message.strip())
        if not coords:
            return "Please provide as: latitude, longitude (e.g. 28.61, 77.20)"
        data["lat"], data["lon"] = coords
        data.setdefault("tz", "IST")
        session["flow"] = None
        return _execute_create_chart(data, session)

    # Shouldn't reach here — reset
    session["flow"] = None
    session["flow_data"] = {}
    return "Something went wrong. Say 'create kundali' to start again."


def _ask_next_create_field(session):
    data = session["flow_data"]
    if "name" not in data:
        data["_step"] = "name"
        return "What's the person's name?"
    if "dob" not in data:
        data["_step"] = "dob"
        return f"Creating chart for {data['name']}.\nDate of birth? (e.g. 15 Jun 1990)"
    if "tob" not in data:
        data["_step"] = "tob"
        return "Time of birth? (e.g. 14:30 or 2:30 PM)"
    if "place" not in data:
        data["_step"] = "place"
        return "Place of birth? (e.g. Delhi, Mumbai, Ranchi)"
    # All fields present
    session["flow"] = None
    return _execute_create_chart(data, session)


def _execute_create_chart(data, session):
    """Compute planetary positions, store in DB, return formatted result."""
    # Resolve city coordinates if missing
    if "lat" not in data:
        city = lookup_city(data.get("place", ""))
        if not city:
            session["flow"] = "create_chart"
            session["flow_data"] = data
            session["flow_data"]["_step"] = "coords"
            return (
                f"I don't have coordinates for '{data.get('place', '')}'.\n"
                "Please provide latitude and longitude (e.g. 28.61, 77.20)"
            )
        data["lat"], data["lon"], data["tz"] = city

    try:
        from kundali_engine.create_kundali import (
            compute_planetary_positions, store_kundali,
        )

        tz = data.get("tz", "IST")
        lagna_sign, lagna_degree, planets = compute_planetary_positions(
            data["dob"], data["tob"], data["lat"], data["lon"], tz,
        )

        person_data = {
            "name": data["name"],
            "dob": data["dob"],
            "tob": data["tob"],
            "lat": data["lat"],
            "lon": data["lon"],
            "place": data.get("place", ""),
            "tz": tz,
        }
        person_id = store_kundali(person_data, lagna_sign, lagna_degree, planets)

        session["active_person_id"] = person_id
        session["active_person_name"] = data["name"]

        lines = [
            f"Chart created for {data['name']} (ID: {person_id})",
            "",
            f"Lagna: {lagna_sign} ({lagna_degree:.1f} deg)",
            "",
        ]

        sun  = next(p for p in planets if p["planet"] == "Sun")
        moon = next(p for p in planets if p["planet"] == "Moon")
        lines.append(f"Sun Sign:  {sun['sign']}  |  Moon Sign: {moon['sign']}")
        lines.append(f"Moon Nakshatra: {moon['nakshatra']} (Pada {moon['nakshatra_pada']})")
        lines.append("")

        lines.append(
            f"{'Planet':<10} {'Sign':<12} {'House':>5} {'Degree':>8} "
            f"{'Nakshatra':<16} {'Dignity':<12} {'R':>2}"
        )
        lines.append("-" * 72)
        for p in planets:
            retro = "R" if p["is_retrograde"] else ""
            lines.append(
                f"{p['planet']:<10} {p['sign']:<12} {p['house']:>5} "
                f"{p['degree_in_sign']:>7.1f}  {p['nakshatra']:<16} "
                f"{p.get('dignity', ''):<12} {retro:>2}"
            )

        lines.append("")
        lines.append(f"Active person is now {data['name']}.")
        return "\n".join(lines)

    except Exception as e:
        return f"Error computing chart: {e}"


# ═════════════════════════════════════════════════════════════════════════════
# SHOW CHART
# ═════════════════════════════════════════════════════════════════════════════

def handle_show_chart(message, session):
    person_name = _extract_person_name(message)

    conn = get_connection()
    try:
        if person_name:
            row = conn.execute(
                "SELECT * FROM person WHERE LOWER(name) LIKE ?",
                (f"%{person_name.lower()}%",),
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT * FROM person WHERE id = ?",
                (session["active_person_id"],),
            ).fetchone()

        if not row:
            return (
                f"No chart found{' for ' + person_name if person_name else ''}. "
                "Use 'list people' to see stored charts."
            )

        person_id = row["id"]
        planets = conn.execute(
            "SELECT * FROM natal_planet WHERE person_id = ? "
            "ORDER BY sidereal_longitude",
            (person_id,),
        ).fetchall()

        lines = [f"Chart for {row['name']} (ID: {person_id})"]
        lines.append(
            f"Born: {row['dob']} at {row['tob']}, "
            f"{row['place_name'] or ''}"
        )
        lines.append(
            f"Lagna: {row['lagna_sign'] or 'N/A'} "
            f"({row['lagna_degree'] or 0:.1f} deg)"
        )
        lines.append("")

        if planets:
            # Sun / Moon summary
            sun  = next((p for p in planets if p["planet"] == "Sun"), None)
            moon = next((p for p in planets if p["planet"] == "Moon"), None)
            if sun and moon:
                lines.append(
                    f"Sun Sign:  {sun['sign']}  |  Moon Sign: {moon['sign']}"
                )
                lines.append(
                    f"Moon Nakshatra: {moon['nakshatra'] or 'N/A'} "
                    f"(Pada {moon['nakshatra_pada'] or '?'})"
                )
                lines.append("")

            lines.append(
                f"{'Planet':<10} {'Sign':<12} {'House':>5} {'Degree':>8} "
                f"{'Nakshatra':<16} {'Dignity':<12} {'R':>2}"
            )
            lines.append("-" * 72)
            for p in planets:
                retro = "R" if p["is_retrograde"] else ""
                lines.append(
                    f"{p['planet']:<10} {p['sign']:<12} "
                    f"{p['house'] or '':>5} "
                    f"{p['degree_in_sign'] or 0:>7.1f}  "
                    f"{p['nakshatra'] or '':<16} "
                    f"{p['dignity'] or '':<12} {retro:>2}"
                )
        else:
            lines.append("No planetary data computed yet.")

        # ── Interpretation sections ──────────────────────────────────────
        if planets:
            try:
                from kundali_engine.agent.interpreter import ChartInterpreter
                interpreter = ChartInterpreter(person_id)
                try:
                    summary = interpreter.chart_summary()
                    if summary:
                        lines.append("")
                        lines.append("=" * 72)
                        lines.append(summary)
                finally:
                    interpreter.close()
            except Exception:
                pass  # interpretation is a bonus; don't break show_chart

        return "\n".join(lines)
    finally:
        conn.close()


# ═════════════════════════════════════════════════════════════════════════════
# LIST PEOPLE
# ═════════════════════════════════════════════════════════════════════════════

def handle_list_people(message, session):
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id, name, dob, place_name FROM person ORDER BY id"
        ).fetchall()

        if not rows:
            return "No charts stored yet. Say 'create kundali' to add one."

        lines = ["Stored charts:", ""]
        lines.append(f"{'ID':>4}  {'Name':<25} {'DOB':<12} {'Place':<20}")
        lines.append("-" * 65)
        for r in rows:
            marker = " <-- active" if r["id"] == session["active_person_id"] else ""
            lines.append(
                f"{r['id']:>4}  {r['name']:<25} "
                f"{r['dob'] or '':<12} {r['place_name'] or '':<20}{marker}"
            )
        return "\n".join(lines)
    finally:
        conn.close()


# ═════════════════════════════════════════════════════════════════════════════
# DASHA INFO
# ═════════════════════════════════════════════════════════════════════════════

def handle_dasha_info(message, session):
    conn = get_connection()
    try:
        person_id = session["active_person_id"]
        name = _get_active_person_name(session)
        today = date.today().isoformat()

        maha = conn.execute(
            "SELECT * FROM dasha WHERE person_id = ? AND level = 'maha' "
            "AND start_date <= ? AND end_date >= ?",
            (person_id, today, today),
        ).fetchone()

        if not maha:
            return (
                f"No dasha data found for {name or 'active person'}. "
                "Dasha computation may not have been run yet."
            )

        lines = [
            f"Dasha periods for {name or 'Person ' + str(person_id)} "
            f"(as of {date.today().strftime('%d %b %Y')}):",
            "",
            f"Mahadasha: {maha['planet']}  "
            f"({maha['start_date']} to {maha['end_date']})",
        ]

        # Active antardasha
        antar = conn.execute(
            "SELECT * FROM dasha WHERE person_id = ? AND level = 'antar' "
            "AND parent_dasha_id = ? AND start_date <= ? AND end_date >= ?",
            (person_id, maha["id"], today, today),
        ).fetchone()

        if antar:
            lines.append(
                f"Antardasha: {antar['planet']}  "
                f"({antar['start_date']} to {antar['end_date']})"
            )
            pratyantar = conn.execute(
                "SELECT * FROM dasha WHERE person_id = ? AND level = 'pratyantar' "
                "AND parent_dasha_id = ? AND start_date <= ? AND end_date >= ?",
                (person_id, antar["id"], today, today),
            ).fetchone()
            if pratyantar:
                lines.append(
                    f"Pratyantar: {pratyantar['planet']}  "
                    f"({pratyantar['start_date']} to {pratyantar['end_date']})"
                )

        # List all antardashas under current mahadasha
        antars = conn.execute(
            "SELECT * FROM dasha WHERE person_id = ? AND level = 'antar' "
            "AND parent_dasha_id = ? ORDER BY start_date",
            (person_id, maha["id"]),
        ).fetchall()

        if antars:
            lines.append("")
            lines.append(f"All sub-periods under {maha['planet']} Mahadasha:")
            lines.append(f"{'Planet':<10} {'Start':<12} {'End':<12} {'Active':>6}")
            lines.append("-" * 44)
            for a in antars:
                active = "<--" if a["start_date"] <= today <= a["end_date"] else ""
                lines.append(
                    f"{a['planet']:<10} {a['start_date']:<12} "
                    f"{a['end_date']:<12} {active:>6}"
                )

        return "\n".join(lines)
    finally:
        conn.close()


# ═════════════════════════════════════════════════════════════════════════════
# TODAY GUIDANCE  (dasha-based; transit scoring not yet built)
# ═════════════════════════════════════════════════════════════════════════════

_GUIDANCE = {
    "Sun": {
        "theme": "Authority, career, government matters, father",
        "do": "Take leadership roles, pursue recognition, deal with authorities",
        "avoid": "Ego conflicts, unnecessary confrontations with bosses",
        "health": "Watch heart, eyes, bones — stay hydrated",
    },
    "Moon": {
        "theme": "Mind, emotions, mother, public dealings",
        "do": "Trust intuition, nurture relationships, connect with people",
        "avoid": "Emotional decisions, overthinking, irregular sleep",
        "health": "Watch stress, water intake, mental peace",
    },
    "Mars": {
        "theme": "Energy, action, property, siblings, courage",
        "do": "Physical exercise, bold initiatives, technical work",
        "avoid": "Arguments, haste, risky driving, anger",
        "health": "Watch blood pressure, injuries, inflammation",
    },
    "Mercury": {
        "theme": "Communication, intellect, business, learning",
        "do": "Study, write, negotiate, learn new skills, analyse data",
        "avoid": "Miscommunication, signing without reading, gossip",
        "health": "Watch skin, nervous system, digestion",
    },
    "Jupiter": {
        "theme": "Wisdom, expansion, teaching, finance, spirituality",
        "do": "Learn, teach, invest wisely, spiritual practice, charity",
        "avoid": "Overcommitment, overindulgence, blind optimism",
        "health": "Watch liver, weight, sugar levels",
    },
    "Venus": {
        "theme": "Relationships, luxury, arts, vehicles, comfort",
        "do": "Enjoy beauty, strengthen relationships, creative pursuits",
        "avoid": "Overspending, overindulgence, relationship drama",
        "health": "Watch kidneys, reproductive health, diabetes",
    },
    "Saturn": {
        "theme": "Discipline, karma, hard work, delays, structure",
        "do": "Be patient, work systematically, serve others, build slowly",
        "avoid": "Shortcuts, laziness, ignoring responsibilities",
        "health": "Watch joints, teeth, chronic conditions — regular checkups",
    },
    "Rahu": {
        "theme": "Ambition, unconventional paths, foreign connections, technology",
        "do": "Explore new opportunities, technology, foreign dealings",
        "avoid": "Deception, addictions, get-rich-quick schemes, confusion",
        "health": "Watch mental health, mysterious ailments, toxins",
    },
    "Ketu": {
        "theme": "Spirituality, detachment, research, past-life karma",
        "do": "Meditate, research deeply, let go of attachments",
        "avoid": "Confusion, aimlessness, ignoring practical matters",
        "health": "Watch infections, allergies, unexplained symptoms",
    },
}


def handle_today_guidance(message, session):
    conn = get_connection()
    try:
        person_id = session["active_person_id"]
        name = _get_active_person_name(session)
        today = date.today().isoformat()

        maha = conn.execute(
            "SELECT planet FROM dasha WHERE person_id = ? AND level = 'maha' "
            "AND start_date <= ? AND end_date >= ?",
            (person_id, today, today),
        ).fetchone()

        antar = None
        if maha:
            antar = conn.execute(
                "SELECT d.planet FROM dasha d JOIN dasha m "
                "ON d.parent_dasha_id = m.id "
                "WHERE d.person_id = ? AND d.level = 'antar' "
                "AND m.level = 'maha' AND m.planet = ? "
                "AND d.start_date <= ? AND d.end_date >= ?",
                (person_id, maha["planet"], today, today),
            ).fetchone()

        if not maha:
            return (
                f"No dasha data for {name or 'active person'} — "
                "can't generate guidance yet."
            )

        maha_planet = maha["planet"]
        antar_planet = antar["planet"] if antar else None

        natal = conn.execute(
            "SELECT * FROM natal_planet WHERE person_id = ? AND planet = ?",
            (person_id, maha_planet),
        ).fetchone()

        lines = [
            f"Daily guidance for {name or 'you'} — "
            f"{date.today().strftime('%d %b %Y')}",
            "",
            f"Current period: {maha_planet}"
            + (f" / {antar_planet}" if antar_planet else ""),
            "",
        ]

        info = _GUIDANCE.get(maha_planet, {})
        lines.append(f"Theme:  {info.get('theme', 'General period')}")

        if natal and natal["dignity"]:
            d = natal["dignity"]
            if d in ("exalted", "moolatrikona", "own"):
                lines.append(
                    f"{maha_planet} is strong in your chart ({d}) "
                    "— positive results likely."
                )
            elif d in ("debilitated", "enemy"):
                lines.append(
                    f"{maha_planet} is challenged in your chart ({d}) "
                    "— extra care needed."
                )

        lines.append("")
        lines.append(f"Do:     {info.get('do', 'Stay balanced')}")
        lines.append(f"Avoid:  {info.get('avoid', 'Excess of any kind')}")
        lines.append(f"Health: {info.get('health', 'Maintain routine')}")

        if antar_planet and antar_planet != maha_planet:
            antar_info = _GUIDANCE.get(antar_planet, {})
            lines.append("")
            lines.append(
                f"Sub-period ({antar_planet}) adds: "
                f"{antar_info.get('theme', 'mixed influences')}"
            )

        lines.append("")
        lines.append(
            "(Transit-based scoring coming soon for more precise daily guidance.)"
        )
        return "\n".join(lines)
    finally:
        conn.close()


# ═════════════════════════════════════════════════════════════════════════════
# TRADING REGIME
# ═════════════════════════════════════════════════════════════════════════════

def handle_trading_regime(message, session):
    try:
        from kundali_engine.engine.astro_regime import compute_astro_regime

        regime = compute_astro_regime(
            db=str(DB_PATH),
            person_id=session["active_person_id"],
        )

        lines = [
            "Market Regime (Astro-based):",
            "",
            f"Direction:  {regime.directional_bias}",
            f"Volatility: {regime.volatility_bias}",
            f"Risk mult:  {regime.risk_multiplier:.1f}x",
            "",
        ]

        if regime.allowed_strategies:
            lines.append(f"Strategies: {', '.join(regime.allowed_strategies)}")
        if regime.favored_sectors:
            lines.append(f"Sectors:    {', '.join(regime.favored_sectors)}")

        if regime.explanation:
            lines.append("")
            lines.append("Reasoning:")
            for e in regime.explanation:
                lines.append(f"  - {e}")

        return "\n".join(lines)
    except Exception as e:
        return f"Could not compute trading regime: {e}"


# ═════════════════════════════════════════════════════════════════════════════
# SECTOR ADVICE
# ═════════════════════════════════════════════════════════════════════════════

def handle_sector_advice(message, session):
    conn = get_connection()
    try:
        person_id = session["active_person_id"]
        today = date.today().isoformat()

        maha = conn.execute(
            "SELECT planet FROM dasha WHERE person_id = ? AND level = 'maha' "
            "AND start_date <= ? AND end_date >= ?",
            (person_id, today, today),
        ).fetchone()

        if not maha:
            return "No dasha data — can't determine favored sectors."

        planet = maha["planet"]

        sectors = conn.execute(
            "SELECT sector, affinity FROM ref_planet_sector "
            "WHERE planet = ?",
            (planet,),
        ).fetchall()

        commodities = conn.execute(
            "SELECT commodity, affinity FROM ref_planet_commodity "
            "WHERE planet = ?",
            (planet,),
        ).fetchall()

        lines = [
            f"Sector/commodity guidance (based on {planet} Mahadasha):",
            "",
        ]

        if sectors:
            lines.append("Favored sectors:")
            for s in sectors:
                lines.append(f"  - {s['sector']} ({s['affinity']})")

        if commodities:
            lines.append("")
            lines.append("Commodity bias:")
            for c in commodities:
                lines.append(f"  - {c['commodity']} ({c['affinity']})")

        if not sectors and not commodities:
            lines.append(
                "No specific sector/commodity mapping found for this planet."
            )

        # Did user ask about a specific commodity?
        msg_lower = message.lower()
        specific = [
            ("gold", "Gold"), ("silver", "Silver"),
            ("crude", "Crude Oil"), ("copper", "Copper"),
        ]
        for keyword, commodity in specific:
            if keyword in msg_lower:
                row = conn.execute(
                    "SELECT * FROM ref_planet_commodity WHERE commodity = ?",
                    (commodity,),
                ).fetchone()
                if row:
                    lines.append("")
                    lines.append(
                        f"{commodity}: Ruled by {row['planet']} "
                        f"({row['affinity']})"
                    )

        return "\n".join(lines)
    finally:
        conn.close()


# ═════════════════════════════════════════════════════════════════════════════
# PLANET INFO
# ═════════════════════════════════════════════════════════════════════════════

def handle_planet_info(message, session):
    planet_name = None
    for p in [
        "Sun", "Moon", "Mars", "Mercury",
        "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
    ]:
        if p.lower() in message.lower():
            planet_name = p
            break

    if not planet_name:
        return "Which planet? Say 'tell me about Saturn' or 'what is Rahu'."

    conn = get_connection()
    try:
        ref = conn.execute(
            "SELECT * FROM ref_planet WHERE name = ?", (planet_name,)
        ).fetchone()

        lines = [f"About {planet_name}:", ""]

        if ref:
            lines.append(f"Nature:           {ref['nature']}")
            lines.append(f"Gender:           {ref['gender']}")
            lines.append(f"Element:          {ref['element'] or 'N/A'}")
            lines.append(f"Dasha years:      {ref['dasha_years']}")
            lines.append(f"Avg daily motion: {ref['avg_daily_motion']} deg/day")
            lines.append(f"Dig bala house:   {ref['dig_bala_house']}")

        # Dignity info
        dignities = conn.execute(
            "SELECT * FROM ref_dignity WHERE planet = ?", (planet_name,)
        ).fetchall()
        if dignities:
            lines.append("")
            for d in dignities:
                lines.append(
                    f"{d['dignity_type'].title()}: {d['sign']} "
                    f"({d['exact_degree']} deg)"
                )

        # Relationships
        rels = conn.execute(
            "SELECT other_planet, relationship "
            "FROM ref_natural_relationship WHERE planet = ?",
            (planet_name,),
        ).fetchall()
        if rels:
            friends = [r["other_planet"] for r in rels if r["relationship"] == "Friend"]
            enemies = [r["other_planet"] for r in rels if r["relationship"] == "Enemy"]
            neutral = [r["other_planet"] for r in rels if r["relationship"] == "Neutral"]
            lines.append("")
            if friends:
                lines.append(f"Friends: {', '.join(friends)}")
            if enemies:
                lines.append(f"Enemies: {', '.join(enemies)}")
            if neutral:
                lines.append(f"Neutral: {', '.join(neutral)}")

        # Show in active person's chart
        person_id = session["active_person_id"]
        natal = conn.execute(
            "SELECT * FROM natal_planet WHERE person_id = ? AND planet = ?",
            (person_id, planet_name),
        ).fetchone()
        if natal:
            name = _get_active_person_name(session)
            placement = f"{natal['sign']}, House {natal['house']}"
            if natal["dignity"]:
                placement += f", {natal['dignity']}"
            if natal["is_retrograde"]:
                placement += " (R)"
            lines.append("")
            lines.append(f"In {name or 'your'}'s chart: {placement}")

        return "\n".join(lines)
    finally:
        conn.close()


# ═════════════════════════════════════════════════════════════════════════════
# SWITCH PERSON
# ═════════════════════════════════════════════════════════════════════════════

def handle_switch_person(message, session):
    msg_lower = message.lower()

    # Extract name after keywords
    name_match = None
    for pattern in [
        r"switch to\s+(.+)", r"set me as\s+(.+)",
        r"use\s+(.+)", r"change to\s+(.+)", r"select\s+(.+)",
    ]:
        m = re.search(pattern, msg_lower)
        if m:
            name_match = m.group(1).strip().rstrip("'s").strip()
            break

    # Check for bare ID
    id_match = re.search(r"\b(\d+)\b", message)

    conn = get_connection()
    try:
        row = None
        if name_match:
            clean = re.sub(
                r"\b(person|chart|kundali|profile)\b", "", name_match
            ).strip()
            if clean:
                row = conn.execute(
                    "SELECT * FROM person WHERE LOWER(name) LIKE ?",
                    (f"%{clean}%",),
                ).fetchone()
        if not row and id_match:
            row = conn.execute(
                "SELECT * FROM person WHERE id = ?",
                (int(id_match.group(1)),),
            ).fetchone()

        if row:
            session["active_person_id"] = row["id"]
            session["active_person_name"] = row["name"]
            return (
                f"Switched to {row['name']} (ID: {row['id']}). "
                "All queries will now use this chart."
            )

        # Not found — show list
        rows = conn.execute(
            "SELECT id, name FROM person ORDER BY id"
        ).fetchall()
        lines = ["Couldn't find that person. Available charts:"]
        for r in rows:
            lines.append(f"  {r['id']}: {r['name']}")
        lines.append("\nSay 'switch to [name]' or 'switch to [ID]'.")
        return "\n".join(lines)
    finally:
        conn.close()


# ═════════════════════════════════════════════════════════════════════════════
# COMPARE  (placeholder)
# ═════════════════════════════════════════════════════════════════════════════

def handle_compare(message, session):
    return (
        "Chart comparison is coming soon!\n"
        "For now, 'switch to [name]' and view charts individually."
    )


# ═════════════════════════════════════════════════════════════════════════════
# INTERNAL HELPERS
# ═════════════════════════════════════════════════════════════════════════════

def _get_active_person_name(session):
    """Lazy-load active person name from DB."""
    if session["active_person_name"]:
        return session["active_person_name"]
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT name FROM person WHERE id = ?",
            (session["active_person_id"],),
        ).fetchone()
        if row:
            session["active_person_name"] = row["name"]
            return row["name"]
    finally:
        conn.close()
    return None


def _extract_person_name(message):
    """Extract person name from 'show X's chart' style messages."""
    msg_lower = message.lower()
    if "my " in msg_lower:
        return None  # use active person

    # "show priyanka's chart"
    m = re.search(
        r"(?:show|view|display|see)\s+(\w+?)(?:'s|s)?\s+(?:chart|kundali)",
        msg_lower,
    )
    if m:
        name = m.group(1)
        if name not in ("the", "a", "my", "this"):
            return name

    # "chart for priyanka"
    m = re.search(r"(?:chart|kundali)\s+(?:for|of)\s+(\w+)", msg_lower)
    if m:
        return m.group(1)

    return None


def _try_parse_inline_chart(message):
    """Try to extract name, dob, tob, place from a single message."""
    data = {}

    # Name: text between "for/of" and "born"
    name_match = re.search(r"(?:for|of)\s+(.+?)\s+born\b", message, re.IGNORECASE)
    if name_match:
        data["name"] = name_match.group(1).strip().title()

    # Date
    date_patterns = [
        r"(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{4})",
        r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+\d{4})",
        r"(\d{4}-\d{2}-\d{2})",
        r"(\d{1,2}[/-]\d{1,2}[/-]\d{4})",
    ]
    for pat in date_patterns:
        m = re.search(pat, message, re.IGNORECASE)
        if m:
            parsed = _parse_date(m.group(1))
            if parsed:
                data["dob"] = parsed
                break

    # Time
    time_patterns = [
        r"(\d{1,2}:\d{2}\s*(?:am|pm|AM|PM))",
        r"(\d{1,2}:\d{2})",
    ]
    for pat in time_patterns:
        m = re.search(pat, message)
        if m:
            parsed = _parse_time(m.group(1))
            if parsed:
                data["tob"] = parsed
                break

    # Place: "in CityName" at end, or last word that's a known city
    place_match = re.search(
        r'\bin\s+([A-Z][a-zA-Z\s]+?)(?:\s*$|\s*["\'])', message
    )
    if place_match:
        data["place"] = place_match.group(1).strip()
    else:
        words = message.split()
        for i in range(len(words) - 1, -1, -1):
            candidate = words[i].strip(".,!?").lower()
            if candidate in CITIES:
                data["place"] = words[i].strip(".,!?")
                break

    return data if data else None


def _parse_date(text):
    """Parse various date formats to YYYY-MM-DD."""
    text = text.strip().replace(",", "")
    for fmt in [
        "%d %b %Y", "%d %B %Y", "%b %d %Y", "%B %d %Y",
        "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y",
    ]:
        try:
            return datetime.strptime(text, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def _parse_time(text):
    """Parse various time formats to HH:MM (24h)."""
    text = text.strip().upper()

    # 6:10AM, 2:30 PM
    m = re.match(r"(\d{1,2}):(\d{2})\s*(AM|PM)", text)
    if m:
        h, mi, ampm = int(m.group(1)), int(m.group(2)), m.group(3)
        if ampm == "PM" and h != 12:
            h += 12
        elif ampm == "AM" and h == 12:
            h = 0
        return f"{h:02d}:{mi:02d}"

    # 14:30
    m = re.match(r"(\d{1,2}):(\d{2})$", text)
    if m:
        h, mi = int(m.group(1)), int(m.group(2))
        if 0 <= h <= 23 and 0 <= mi <= 59:
            return f"{h:02d}:{mi:02d}"

    return None


def _parse_coords(text):
    """Parse 'lat, lon' from text."""
    m = re.match(r"(-?[\d.]+)\s*,\s*(-?[\d.]+)", text.strip())
    if m:
        return float(m.group(1)), float(m.group(2))
    return None


# ═════════════════════════════════════════════════════════════════════════════
# INTERPRET  (chart-based life questions — the Vedic Life Coach)
# ═════════════════════════════════════════════════════════════════════════════

def handle_interpret(message, session):
    """Handle open-ended chart questions using the interpretation engine."""
    from kundali_engine.agent.interpreter import ChartInterpreter

    person_id = session["active_person_id"]
    interpreter = ChartInterpreter(person_id)

    try:
        msg_lower = message.lower()

        # Special entry points
        if any(w in msg_lower for w in ("universe", "cosmic", "telling me")):
            response = interpreter.universe_message()
        elif any(w in msg_lower for w in (
            "personality", "who am i", "what am i", "my traits",
            "my character", "about me", "describe me",
        )):
            response = interpreter.personality_profile()
        else:
            response = interpreter.interpret(message)

        # Log the event
        themes = interpreter._detect_themes(message)
        event_store.log_event(
            session_id=session["session_id"],
            person_id=person_id,
            question=message,
            intent="interpret",
            themes=themes or None,
            planets=[p for p in interpreter.planets.keys()] if interpreter.planets else None,
            houses=[d["house"] for d in interpreter.planets.values()] if interpreter.planets else None,
            variants_used=interpreter.variants_used or None,
            response=response,
        )

        return response
    finally:
        interpreter.close()


# ═════════════════════════════════════════════════════════════════════════════
# RATE  (user feedback for RL variant selection)
# ═════════════════════════════════════════════════════════════════════════════

def handle_rate(message, session):
    """Record user rating for the last response."""
    # Extract rating number
    m = re.search(r"\b([1-5])\b", message)
    if not m:
        # Check for word-based ratings
        msg_lower = message.lower()
        if any(w in msg_lower for w in ("helpful", "good", "great", "excellent", "love")):
            rating = 5
        elif any(w in msg_lower for w in ("not helpful", "bad", "poor", "wrong")):
            rating = 2
        else:
            return "Please rate from 1 to 5 (e.g. 'rate 4' or '5 stars')."
    else:
        rating = int(m.group(1))

    last_event_id = event_store.get_last_event_id(session["session_id"])
    if not last_event_id:
        return "Nothing to rate yet. Ask me a question first!"

    # Extract optional text feedback
    feedback_text = re.sub(
        r"\b(?:rate|rating|stars?|thumbs|[1-5])\b", "", message, flags=re.IGNORECASE
    ).strip() or None

    event_store.log_feedback(last_event_id, rating, feedback_text)

    stars = "*" * rating + "." * (5 - rating)
    return f"Thanks! Recorded your rating: [{stars}] ({rating}/5)\nThis helps me give better readings."
