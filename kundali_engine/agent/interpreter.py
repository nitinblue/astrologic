"""
Chart Interpretation Engine — Vedic Life Coach.

Pure rule-based interpretation: no LLM. Maps life themes through a
person's natal chart and generates personalized coaching text.
Multiple text variants per rule; RL (epsilon-greedy) selects the best
variant based on accumulated user feedback.
"""
import json
import random
import re
from datetime import date

from kundali_engine.core.database.connection import get_connection
from kundali_engine.agent import event_store


class ChartInterpreter:
    """Reads a person's chart and produces personalized interpretations."""

    EPSILON = 0.20  # exploration rate for variant selection

    def __init__(self, person_id):
        self.person_id = person_id
        self.conn = get_connection()

        # Load person
        self.person = self.conn.execute(
            "SELECT * FROM person WHERE id = ?", (person_id,)
        ).fetchone()

        # Load natal planets (dict keyed by planet name)
        rows = self.conn.execute(
            "SELECT * FROM natal_planet WHERE person_id = ?", (person_id,)
        ).fetchall()
        self.planets = {r["planet"]: dict(r) for r in rows}

        # Load current dasha
        today = date.today().isoformat()
        self.maha = self.conn.execute(
            "SELECT * FROM dasha WHERE person_id = ? AND level = 'maha' "
            "AND start_date <= ? AND end_date >= ?",
            (person_id, today, today),
        ).fetchone()

        self.antar = None
        if self.maha:
            self.antar = self.conn.execute(
                "SELECT * FROM dasha WHERE person_id = ? AND level = 'antar' "
                "AND parent_dasha_id = ? AND start_date <= ? AND end_date >= ?",
                (person_id, self.maha["id"], today, today),
            ).fetchone()

        # Track which variants we select (for event logging)
        self.variants_used = []

    def close(self):
        self.conn.close()

    # ── Main entry points ─────────────────────────────────────────────────

    def interpret(self, question):
        """Question -> personalized interpretation text."""
        themes = self._detect_themes(question)
        sections = []

        if not themes:
            # No specific theme matched — give general personality reading
            return self.personality_profile()

        for theme in themes[:3]:  # cap at 3 themes per question
            section = self._interpret_theme(theme)
            if section:
                sections.append(section)

        # Always add karmic direction and dasha context
        karmic = self._karmic_direction()
        if karmic:
            sections.append(karmic)

        dasha_ctx = self._dasha_context(themes)
        if dasha_ctx:
            sections.append(dasha_ctx)

        if not sections:
            return self.personality_profile()

        return self._compose(question, sections)

    def universe_message(self):
        """Holistic reading: Rahu/Ketu + strong/weak planets + dasha."""
        sections = []

        karmic = self._karmic_direction()
        if karmic:
            sections.append(karmic)

        # Strongest and weakest planets
        strong = self._strong_planets()
        weak = self._weak_planets()

        if strong:
            names = ", ".join(strong)
            sections.append(
                f"YOUR NATURAL GIFTS\n"
                f"Your strongest planets are {names}. "
                f"These are the areas where life flows easily for you — "
                f"lean into them, especially during uncertain times."
            )

        if weak:
            names = ", ".join(weak)
            sections.append(
                f"YOUR GROWTH EDGES\n"
                f"Your chart shows {names} as areas needing conscious effort. "
                f"These aren't punishments — they're where your biggest growth happens. "
                f"The discomfort you feel here is the universe's curriculum for you."
            )

        # Planet concentrations
        house_counts = {}
        for p, data in self.planets.items():
            h = data["house"]
            house_counts.setdefault(h, []).append(p)

        crowded = [(h, ps) for h, ps in house_counts.items() if len(ps) >= 3]
        if crowded:
            for h, ps in crowded:
                house_info = self.conn.execute(
                    "SELECT english_name, core_domain FROM ref_house WHERE house_number = ?",
                    (h,)
                ).fetchone()
                domain = house_info["core_domain"] if house_info else f"House {h}"
                sections.append(
                    f"ENERGY CONCENTRATION\n"
                    f"{', '.join(ps)} are all in House {h} ({domain}). "
                    f"This area of life gets intense attention — for better or worse. "
                    f"It's where your life lessons are concentrated."
                )

        dasha_ctx = self._dasha_context([])
        if dasha_ctx:
            sections.append(dasha_ctx)

        name = self.person["name"] if self.person else "you"
        header = f"What the universe is telling {name}:\n"
        return header + "\n\n".join(sections)

    def personality_profile(self):
        """Lagna + Moon sign + planet strengths -> traits/strengths/weaknesses."""
        if not self.person:
            return "No chart data found."

        name = self.person["name"]
        lagna = self.person["lagna_sign"]
        sections = []

        # Lagna personality
        if lagna:
            lagna_info = self.conn.execute(
                "SELECT * FROM ref_sign WHERE name = ?", (lagna,)
            ).fetchone()
            if lagna_info:
                sections.append(
                    f"PERSONALITY FOUNDATION ({lagna} Rising)\n"
                    f"As a {lagna} ascendant ({lagna_info['element']}, "
                    f"{lagna_info['modality']}), your core personality is shaped by "
                    f"{lagna_info['ruler']}. You naturally approach life with "
                    f"{'initiative and fire' if lagna_info['element'] == 'Fire' else ''}"
                    f"{'practicality and groundedness' if lagna_info['element'] == 'Earth' else ''}"
                    f"{'intellect and adaptability' if lagna_info['element'] == 'Air' else ''}"
                    f"{'emotion and intuition' if lagna_info['element'] == 'Water' else ''}."
                )

        # Moon sign — emotional nature
        moon = self.planets.get("Moon")
        if moon:
            sections.append(
                f"EMOTIONAL NATURE (Moon in {moon['sign']}, House {moon['house']})\n"
                f"Your emotional core is {moon['sign']}. This is how you feel, "
                f"react, and process experiences internally. "
                f"{'Your emotions are stable and grounded.' if moon.get('dignity') in ('exalted', 'own', 'moolatrikona') else ''}"
                f"{'Your emotions can be intense — self-awareness helps you channel them.' if moon.get('dignity') in ('debilitated', 'enemy') else ''}"
            )

        # Sun sign — ego and identity
        sun = self.planets.get("Sun")
        if sun:
            sections.append(
                f"IDENTITY & EGO (Sun in {sun['sign']}, House {sun['house']})\n"
                f"Your sense of self comes alive through House {sun['house']} matters. "
                f"This is where you seek recognition and feel most 'you'."
            )

        # Strengths from strong planets
        strong = self._strong_planets()
        if strong:
            strength_lines = []
            for p in strong:
                data = self.planets.get(p)
                if data:
                    meaning = self._get_planet_house_meaning(p, data["house"])
                    if meaning and meaning.get("when_strong"):
                        strength_lines.append(f"  {p} (House {data['house']}): {meaning['when_strong']}")
            if strength_lines:
                sections.append("YOUR STRENGTHS\n" + "\n".join(strength_lines))

        # Growth areas from weak planets
        weak = self._weak_planets()
        if weak:
            weak_lines = []
            for p in weak:
                data = self.planets.get(p)
                if data:
                    meaning = self._get_planet_house_meaning(p, data["house"])
                    if meaning and meaning.get("when_weak"):
                        weak_lines.append(f"  {p} (House {data['house']}): {meaning['when_weak']}")
            if weak_lines:
                sections.append("AREAS FOR GROWTH\n" + "\n".join(weak_lines))

        # Karmic direction
        karmic = self._karmic_direction()
        if karmic:
            sections.append(karmic)

        # Current dasha
        dasha_ctx = self._dasha_context([])
        if dasha_ctx:
            sections.append(dasha_ctx)

        header = f"Personality profile for {name}:\n"
        return header + "\n\n".join(sections) if sections else f"Chart loaded for {name} but no planetary data found."

    # ── Compact chart summary (for show_chart display) ──────────────────

    def chart_summary(self):
        """Return a compact interpretation suitable for appending to show_chart output."""
        if not self.person:
            return ""

        sections = []

        # 1. Personality snapshot: Lagna element/ruler, Moon emotional nature, Sun identity
        lagna = self.person["lagna_sign"]
        if lagna:
            lagna_info = self.conn.execute(
                "SELECT * FROM ref_sign WHERE name = ?", (lagna,)
            ).fetchone()
            if lagna_info:
                element_trait = {
                    "Fire": "initiative, courage, and directness",
                    "Earth": "practicality, stability, and groundedness",
                    "Air": "intellect, communication, and adaptability",
                    "Water": "intuition, emotion, and sensitivity",
                }.get(lagna_info["element"], "balanced energy")
                sections.append(
                    f"PERSONALITY SNAPSHOT\n"
                    f"  {lagna} Rising ({lagna_info['element']}, ruled by {lagna_info['ruler']})"
                    f" — you lead with {element_trait}."
                )

        moon = self.planets.get("Moon")
        if moon:
            sections[-1] += f"\n  Moon in {moon['sign']} (H{moon['house']}) — your emotional core is {moon['sign']}."

        sun = self.planets.get("Sun")
        if sun:
            sections[-1] += f"\n  Sun in {sun['sign']} (H{sun['house']}) — your identity shines through House {sun['house']} matters."

        # 2. Strengths: planets in exalted/own/moolatrikona with when_strong text
        strong = self._strong_planets()
        if strong:
            strength_lines = []
            for p in strong:
                data = self.planets.get(p)
                if data:
                    meaning = self._get_planet_house_meaning(p, data["house"])
                    text = meaning["when_strong"] if meaning and meaning.get("when_strong") else f"strong in {data['sign']} ({data.get('dignity', '')})"
                    strength_lines.append(f"  {p} (H{data['house']}, {data.get('dignity', '')}): {text}")
            if strength_lines:
                sections.append("STRENGTHS\n" + "\n".join(strength_lines))

        # 3. Growth areas: planets in debilitated/enemy with when_weak text
        weak = self._weak_planets()
        if weak:
            weak_lines = []
            for p in weak:
                data = self.planets.get(p)
                if data:
                    meaning = self._get_planet_house_meaning(p, data["house"])
                    text = meaning["when_weak"] if meaning and meaning.get("when_weak") else f"challenged in {data['sign']} ({data.get('dignity', '')})"
                    weak_lines.append(f"  {p} (H{data['house']}, {data.get('dignity', '')}): {text}")
            if weak_lines:
                sections.append("GROWTH AREAS\n" + "\n".join(weak_lines))

        # 4. Karmic direction: Rahu/Ketu with variant selection
        rahu = self.planets.get("Rahu")
        if rahu:
            rh = rahu["house"]
            vid = self._pick_variant("Rahu", rh, "rahu_ketu")
            axis = self.conn.execute(
                "SELECT * FROM ref_rahu_ketu_axis WHERE rahu_house = ? AND variant_id = ?",
                (rh, vid),
            ).fetchone()
            if not axis:
                axis = self.conn.execute(
                    "SELECT * FROM ref_rahu_ketu_axis WHERE rahu_house = ? AND variant_id = 1",
                    (rh,),
                ).fetchone()
            if axis:
                ketu = self.planets.get("Ketu")
                kh = ketu["house"] if ketu else "?"
                sections.append(
                    f"KARMIC DIRECTION (Rahu H{rahu['house']} / Ketu H{kh})\n"
                    f"  From: {axis['karmic_from']}  ->  To: {axis['karmic_to']}\n"
                    f"  Lesson: {axis['life_lesson']}"
                )

        # 5. Current dasha period
        if self.maha:
            maha_planet = self.maha["planet"]
            antar_planet = self.antar["planet"] if self.antar else None
            natal = self.planets.get(maha_planet)
            dignity_note = ""
            if natal and natal.get("dignity"):
                d = natal["dignity"]
                if d in ("exalted", "moolatrikona", "own"):
                    dignity_note = f" — strong ({d}), positive results"
                elif d in ("debilitated", "enemy"):
                    dignity_note = f" — challenged ({d}), requires patience"
            period_str = maha_planet + (f" / {antar_planet}" if antar_planet else "")
            sections.append(
                f"CURRENT PERIOD: {period_str}{dignity_note}"
            )

        if not sections:
            return ""

        return "\n\n".join(sections)

    # ── Theme detection ───────────────────────────────────────────────────

    def _detect_themes(self, question):
        """Match question keywords against ref_life_theme rows."""
        q_lower = question.lower()
        rows = self.conn.execute(
            "SELECT theme, display_name FROM ref_life_theme"
        ).fetchall()

        # Build keyword map from theme names and display names
        matches = []
        for row in rows:
            theme = row["theme"]
            display = row["display_name"].lower()

            # Check theme key (underscores -> spaces too)
            theme_words = theme.replace("_", " ").split()
            display_words = display.split()

            score = 0
            for w in theme_words + display_words:
                if len(w) > 2 and w in q_lower:
                    score += 1

            if score > 0:
                matches.append((score, theme))

        # Also check specific keyword mappings for natural language
        keyword_map = {
            "job": "career", "work": "career", "promotion": "career",
            "fired": "job_loss", "layoff": "job_loss", "laid off": "job_loss",
            "ai": "technology_ai", "automation": "technology_ai", "tech": "technology_ai",
            "love": "relationships", "partner": "relationships", "dating": "relationships",
            "wife": "marriage", "husband": "marriage", "married": "marriage", "marry": "marriage",
            "sick": "health", "disease": "health", "doctor": "health", "body": "health",
            "anxiety": "mental_health", "stress": "mental_health", "depress": "mental_health",
            "worry": "mental_health", "peace": "mental_health",
            "money": "wealth", "rich": "wealth", "earn": "wealth", "income": "wealth",
            "invest": "investment", "stock": "finance_markets", "mutual fund": "investment",
            "gold": "commodities_gold", "silver": "commodities_silver",
            "crude": "commodities_crude", "oil": "commodities_crude",
            "house": "real_estate", "flat": "real_estate", "property": "real_estate",
            "land": "real_estate", "apartment": "real_estate",
            "meditat": "spirituality", "spiritual": "spirituality", "dharma": "spirituality",
            "god": "spirituality", "pray": "spirituality", "soul": "spirituality",
            "child": "children", "son": "children", "daughter": "children", "kid": "children",
            "study": "education", "learn": "education", "exam": "education", "degree": "education",
            "travel": "foreign_travel", "abroad": "foreign_travel", "visa": "foreign_travel",
            "strength": "strengths", "strong": "strengths", "talent": "strengths",
            "weakness": "weaknesses", "flaw": "weaknesses", "blind spot": "weaknesses",
            "personality": "personality", "trait": "personality", "character": "personality",
            "who am i": "personality", "what am i": "personality",
            "purpose": "life_purpose", "why am i": "life_purpose", "meaning": "life_purpose",
            "karma": "karma", "past life": "karma",
            "universe": "karma",  # "what is the universe telling me"
            "courage": "courage", "confidence": "courage", "fear": "courage",
            "enemy": "enemies", "rival": "enemies", "competition": "enemies",
            "reputation": "reputation", "respect": "reputation", "image": "reputation",
            "business": "business", "startup": "business", "entrepreneur": "business",
            "leader": "leadership", "manage": "leadership",
            "debt": "debt", "loan": "debt", "emi": "debt",
            "father": "family", "mother": "family", "parent": "family",
            "sibling": "family", "brother": "family", "sister": "family",
            "transform": "transformation", "change": "transformation",
            "crisis": "transformation",
            "emotion": "emotional_nature", "feeling": "emotional_nature",
            "vehicle": "vehicle", "bike": "vehicle",
            "court": "legal", "lawsuit": "legal", "legal": "legal",
            "inheritance": "inheritance", "ancestral": "inheritance",
            "workplace": "career",
            "prepare": "career",  # "how should I prepare"
        }

        for keyword, theme in keyword_map.items():
            # Use word boundary check to avoid "car" matching "career" etc.
            if re.search(r'\b' + re.escape(keyword), q_lower) and not any(t == theme for _, t in matches):
                matches.append((1, theme))

        # Sort by score, deduplicate
        matches.sort(key=lambda x: -x[0])
        seen = set()
        result = []
        for _, theme in matches:
            if theme not in seen:
                seen.add(theme)
                result.append(theme)

        return result

    # ── Theme interpretation ──────────────────────────────────────────────

    def _interpret_theme(self, theme):
        """For a theme, find relevant planets/houses, read chart, assemble text."""
        theme_row = self.conn.execute(
            "SELECT * FROM ref_life_theme WHERE theme = ?", (theme,)
        ).fetchone()
        if not theme_row:
            return None

        display_name = theme_row["display_name"]
        relevant_planets = json.loads(theme_row["relevant_planets"])
        relevant_houses = json.loads(theme_row["relevant_houses"])

        lines = [f"{display_name.upper()}"]
        interpretations = []

        for planet_name in relevant_planets:
            natal = self.planets.get(planet_name)
            if not natal:
                continue

            house = natal["house"]
            dignity = natal.get("dignity")
            is_strong = dignity in ("exalted", "moolatrikona", "own")
            is_weak = dignity in ("debilitated", "enemy")

            # Planet-theme meaning
            theme_meaning = self._get_planet_theme_meaning(planet_name, theme)
            if theme_meaning:
                text = theme_meaning["meaning"]
                if is_strong and theme_meaning.get("when_strong"):
                    text += " " + theme_meaning["when_strong"]
                elif is_weak and theme_meaning.get("when_weak"):
                    text += " " + theme_meaning["when_weak"]
                interpretations.append(f"  {planet_name} ({natal['sign']}, H{house}): {text}")

            # Planet-house meaning (if this house is relevant to the theme)
            elif house in relevant_houses:
                house_meaning = self._get_planet_house_meaning(planet_name, house)
                if house_meaning:
                    text = house_meaning["meaning"]
                    if is_strong and house_meaning.get("when_strong"):
                        text += " " + house_meaning["when_strong"]
                    elif is_weak and house_meaning.get("when_weak"):
                        text += " " + house_meaning["when_weak"]
                    interpretations.append(f"  {planet_name} ({natal['sign']}, H{house}): {text}")

        if interpretations:
            lines.extend(interpretations)
        else:
            lines.append(f"  Your chart doesn't show strong activation for {display_name} right now.")

        return "\n".join(lines)

    # ── Karmic direction (Rahu/Ketu axis) ─────────────────────────────────

    def _karmic_direction(self):
        """Rahu/Ketu axis interpretation with RL variant selection."""
        rahu = self.planets.get("Rahu")
        if not rahu:
            return None

        rahu_house = rahu["house"]
        variant_id = self._pick_variant("Rahu", rahu_house, "rahu_ketu")

        axis = self.conn.execute(
            "SELECT * FROM ref_rahu_ketu_axis WHERE rahu_house = ? AND variant_id = ?",
            (rahu_house, variant_id),
        ).fetchone()

        if not axis:
            # Fallback to variant 1
            axis = self.conn.execute(
                "SELECT * FROM ref_rahu_ketu_axis WHERE rahu_house = ? AND variant_id = 1",
                (rahu_house,),
            ).fetchone()
            variant_id = 1

        if not axis:
            return None

        self.variants_used.append({
            "planet": "Rahu", "house": rahu_house,
            "variant_id": variant_id, "type": "rahu_ketu",
        })

        ketu = self.planets.get("Ketu")
        ketu_house = ketu["house"] if ketu else "?"

        lines = [
            f"YOUR KARMIC DIRECTION (Rahu H{rahu_house} / Ketu H{ketu_house})",
            f"  Where you've been: {axis['karmic_from']}",
            f"  Where you're going: {axis['karmic_to']}",
            f"  Life lesson: {axis['life_lesson']}",
        ]
        return "\n".join(lines)

    # ── Dasha context ─────────────────────────────────────────────────────

    def _dasha_context(self, themes):
        """What current dasha activates, especially for the given themes."""
        if not self.maha:
            return None

        maha_planet = self.maha["planet"]
        antar_planet = self.antar["planet"] if self.antar else None

        lines = [
            f"CURRENT PERIOD ({maha_planet}"
            + (f" / {antar_planet}" if antar_planet else "")
            + ")",
        ]

        # Check if dasha planet is relevant to any detected themes
        if themes:
            for theme in themes[:2]:
                theme_row = self.conn.execute(
                    "SELECT relevant_planets FROM ref_life_theme WHERE theme = ?",
                    (theme,)
                ).fetchone()
                if theme_row:
                    relevant = json.loads(theme_row["relevant_planets"])
                    if maha_planet in relevant:
                        lines.append(
                            f"  Your {maha_planet} mahadasha directly activates "
                            f"the {theme.replace('_', ' ')} area of your life right now."
                        )
                        break

        # General dasha guidance
        natal = self.planets.get(maha_planet)
        if natal:
            dignity = natal.get("dignity", "")
            if dignity in ("exalted", "moolatrikona", "own"):
                lines.append(
                    f"  {maha_planet} is strong in your chart ({dignity}) — "
                    f"this period brings positive results with effort."
                )
            elif dignity in ("debilitated", "enemy"):
                lines.append(
                    f"  {maha_planet} is challenged in your chart ({dignity}) — "
                    f"this period requires patience and conscious effort."
                )
            else:
                lines.append(
                    f"  {maha_planet} is in {natal['sign']} (H{natal['house']}) — "
                    f"moderate influence, results depend on your actions."
                )

        if antar_planet and antar_planet != maha_planet:
            lines.append(
                f"  Sub-period of {antar_planet} adds its flavor — "
                f"pay attention to {antar_planet}-related matters too."
            )

        return "\n".join(lines)

    # ── Variant selection (RL) ────────────────────────────────────────────

    def _pick_variant(self, planet, key, key_type="house"):
        """
        RL: select best variant based on past feedback scores.
        Epsilon-greedy: 20% exploration, 80% exploitation.
        """
        scores = event_store.get_variant_scores(planet, key, key_type)

        if not scores:
            return random.choice([1, 2, 3])  # no feedback yet — rotate randomly

        if random.random() < self.EPSILON:
            # Explore: random variant
            return random.choice(list(scores.keys()))

        # Exploit: best-rated variant
        return max(scores, key=scores.get)

    # ── DB lookups with variant selection ─────────────────────────────────

    def _get_planet_house_meaning(self, planet, house):
        """Look up planet-house meaning, selecting best variant."""
        variant_id = self._pick_variant(planet, house, "house")

        row = self.conn.execute(
            "SELECT * FROM ref_planet_house_meaning "
            "WHERE planet = ? AND house = ? AND variant_id = ?",
            (planet, house, variant_id),
        ).fetchone()

        if not row:
            # Fallback to variant 1
            row = self.conn.execute(
                "SELECT * FROM ref_planet_house_meaning "
                "WHERE planet = ? AND house = ? AND variant_id = 1",
                (planet, house),
            ).fetchone()
            variant_id = 1

        if row:
            self.variants_used.append({
                "planet": planet, "house": house,
                "variant_id": variant_id, "type": "house",
            })
            return dict(row)
        return None

    def _get_planet_theme_meaning(self, planet, theme):
        """Look up planet-theme meaning, selecting best variant."""
        variant_id = self._pick_variant(planet, theme, "theme")

        row = self.conn.execute(
            "SELECT * FROM ref_planet_theme_meaning "
            "WHERE planet = ? AND theme = ? AND variant_id = ?",
            (planet, theme, variant_id),
        ).fetchone()

        if not row:
            row = self.conn.execute(
                "SELECT * FROM ref_planet_theme_meaning "
                "WHERE planet = ? AND theme = ? AND variant_id = 1",
                (planet, theme),
            ).fetchone()
            variant_id = 1

        if row:
            self.variants_used.append({
                "planet": planet, "theme": theme,
                "variant_id": variant_id, "type": "theme",
            })
            return dict(row)
        return None

    # ── Helper methods ────────────────────────────────────────────────────

    def _strong_planets(self):
        """Planets in exalted, own, or moolatrikona dignity."""
        return [
            p for p, data in self.planets.items()
            if data.get("dignity") in ("exalted", "moolatrikona", "own")
        ]

    def _weak_planets(self):
        """Planets in debilitated or enemy dignity."""
        return [
            p for p, data in self.planets.items()
            if data.get("dignity") in ("debilitated", "enemy")
        ]

    def _compose(self, question, sections):
        """Join sections into coherent plain-text response."""
        name = self.person["name"] if self.person else "you"
        header = f"Reading for {name}:\n"
        return header + "\n\n".join(sections)
