# Vedic Astrology (Jyotish Shastra) — Deep Reference

> This document is the conceptual backbone of the AstroLogic project.
> Every section maps to something we can (and will) build in code.

---

## Table of Contents

1. [What is Jyotish](#1-what-is-jyotish)
2. [Sidereal vs Tropical — Ayanamsa](#2-sidereal-vs-tropical--ayanamsa)
3. [The 12 Rashis (Signs)](#3-the-12-rashis-signs)
4. [The 9 Grahas (Planets)](#4-the-9-grahas-planets)
5. [The 12 Bhavas (Houses)](#5-the-12-bhavas-houses)
6. [Lagna — The Anchor](#6-lagna--the-anchor)
7. [The 27 Nakshatras (Lunar Mansions)](#7-the-27-nakshatras-lunar-mansions)
8. [Planetary Dignity — Strength and Weakness](#8-planetary-dignity--strength-and-weakness)
9. [Planetary Relationships (Naisargika & Tatkalika)](#9-planetary-relationships)
10. [Aspects (Drishti)](#10-aspects-drishti)
11. [Shadbala — Six-Fold Strength](#11-shadbala--six-fold-strength)
12. [Yogas — Planetary Combinations](#12-yogas--planetary-combinations)
13. [Vimshottari Dasha — The Timing Engine](#13-vimshottari-dasha--the-timing-engine)
14. [Transits (Gochar)](#14-transits-gochar)
15. [Ashtakavarga — Transit Scoring](#15-ashtakavarga--transit-scoring)
16. [Divisional Charts (Vargas)](#16-divisional-charts-vargas)
17. [Mundane & Financial Astrology](#17-mundane--financial-astrology)
18. [Putting It All Together — The Engine Model](#18-putting-it-all-together--the-engine-model)
19. [Nitin's Chart — Worked Example](#19-nitins-chart--worked-example)
20. [Buildable Modules Map](#20-buildable-modules-map)

---

## 1. What is Jyotish

Jyotish (Sanskrit: ज्योतिष, "science of light") is the Indian system of astronomy-astrology. Unlike Western astrology which evolved toward psychology, Jyotish remained predictive and event-oriented.

**Core premise:** The positions of celestial bodies at the moment of birth encode the karmic blueprint of a life. Planetary periods (Dashas) and transits activate different parts of this blueprint over time.

**Why it matters for this project:** Jyotish is a rule-based system. Every interpretation follows from:
- **What** (planet) is acting
- **How** (sign) it behaves
- **Where** (house) it acts
- **When** (dasha + transit) it activates
- **How strongly** (dignity + shadbala) it delivers

This is fundamentally a scoring engine. That's what we're building.

---

## 2. Sidereal vs Tropical — Ayanamsa

### The Problem
The Earth's axis wobbles (precession). Over ~26,000 years the vernal equinox drifts backward through the zodiac. As of 2026, the drift is approximately **24 degrees**.

### Two Systems

| | Tropical (Western) | Sidereal (Vedic) |
|---|---|---|
| Reference point | Vernal equinox (0° Aries = March equinox) | Fixed stars (0° Aries = star Ashwini) |
| Drift | Moves with precession | Stays fixed to star background |
| Result today | ~24° ahead of sidereal | The "real" sky position |

### Ayanamsa
The angular difference between tropical and sidereal is called **Ayanamsa**.

| Ayanamsa System | Value (~2026) | Usage |
|---|---|---|
| **Lahiri** (Chitrapaksha) | ~24°07' | Indian government standard, most common |
| Raman | ~22°30' | B.V. Raman school |
| KP (Krishnamurti) | ~23°57' | KP astrology system |
| True Chitrapaksha | ~24°07' | Spica-based calculation |

**For this project:** We use **Lahiri** (already set as default in `BirthData.ayanamsa`).

**Conversion formula:**
```
sidereal_longitude = tropical_longitude - ayanamsa_value
```

**Code implication:** Any ephemeris library (Swiss Ephemeris, Skyfield) gives tropical positions. We must subtract the ayanamsa to get Vedic positions. This is the single most critical computation in the system.

---

## 3. The 12 Rashis (Signs)

Each rashi spans exactly 30° of the 360° zodiac.

| # | Rashi | Sanskrit | Symbol | Element | Modality | Ruler | Degrees |
|---|-------|----------|--------|---------|----------|-------|---------|
| 1 | Aries | मेष (Mesha) | Ram | Fire | Cardinal (Chara) | Mars | 0°–30° |
| 2 | Taurus | वृषभ (Vrishabha) | Bull | Earth | Fixed (Sthira) | Venus | 30°–60° |
| 3 | Gemini | मिथुन (Mithuna) | Twins | Air | Mutable (Dvisvabhava) | Mercury | 60°–90° |
| 4 | Cancer | कर्क (Karka) | Crab | Water | Cardinal | Moon | 90°–120° |
| 5 | Leo | सिंह (Simha) | Lion | Fire | Fixed | Sun | 120°–150° |
| 6 | Virgo | कन्या (Kanya) | Maiden | Earth | Mutable | Mercury | 150°–180° |
| 7 | Libra | तुला (Tula) | Scales | Air | Cardinal | Venus | 180°–210° |
| 8 | Scorpio | वृश्चिक (Vrishchika) | Scorpion | Water | Fixed | Mars | 210°–240° |
| 9 | Sagittarius | धनु (Dhanu) | Archer | Fire | Mutable | Jupiter | 240°–270° |
| 10 | Capricorn | मकर (Makara) | Crocodile | Earth | Cardinal | Saturn | 270°–300° |
| 11 | Aquarius | कुंभ (Kumbha) | Pot | Air | Fixed | Saturn | 300°–330° |
| 12 | Pisces | मीन (Meena) | Fish | Water | Mutable | Jupiter | 330°–360° |

### Elements (Tatva)

| Element | Signs | Nature |
|---------|-------|--------|
| **Fire** (Agni) | Aries, Leo, Sagittarius | Action, energy, initiative, aggression |
| **Earth** (Prithvi) | Taurus, Virgo, Capricorn | Stability, material, practical, slow |
| **Air** (Vayu) | Gemini, Libra, Aquarius | Intellect, communication, movement |
| **Water** (Jala) | Cancer, Scorpio, Pisces | Emotion, intuition, transformation |

### Modalities (Guna)

| Modality | Signs | Nature |
|----------|-------|--------|
| **Cardinal** (Chara) | Aries, Cancer, Libra, Capricorn | Initiating, dynamic, restless |
| **Fixed** (Sthira) | Taurus, Leo, Scorpio, Aquarius | Stable, persistent, resistant to change |
| **Mutable** (Dvisvabhava) | Gemini, Virgo, Sagittarius, Pisces | Adaptable, flexible, dual-natured |

### Sign Characteristics — Detailed

| Sign | Gender | Nature | Rising Body Part | Key Themes |
|------|--------|--------|-----------------|------------|
| Aries | Male | Cruel (Krura) | Head | Initiative, combat, leadership |
| Taurus | Female | Gentle (Saumya) | Face/Neck | Wealth, beauty, stability |
| Gemini | Male | Cruel | Arms/Shoulders | Communication, duality, trade |
| Cancer | Female | Gentle | Chest | Nurturing, home, emotions |
| Leo | Male | Cruel | Stomach | Authority, ego, governance |
| Virgo | Female | Gentle | Hips | Analysis, service, health |
| Libra | Male | Cruel | Lower abdomen | Balance, trade, relationships |
| Scorpio | Female | Gentle | Genitals | Secrets, transformation, crisis |
| Sagittarius | Male | Cruel | Thighs | Philosophy, law, long journeys |
| Capricorn | Female | Gentle | Knees | Structure, discipline, karma |
| Aquarius | Male | Cruel | Calves | Innovation, groups, detachment |
| Pisces | Female | Gentle | Feet | Spirituality, dissolution, moksha |

---

## 4. The 9 Grahas (Planets)

Vedic astrology uses 9 bodies: 7 visible planets + 2 shadow points (lunar nodes).

### Basic Properties

| Graha | Sanskrit | Symbol | Nature | Gender | Element | Governs |
|-------|----------|--------|--------|--------|---------|---------|
| **Sun** | सूर्य (Surya) | ☉ | Malefic (Krura) | Male | Fire | Soul, authority, father, government |
| **Moon** | चंद्र (Chandra) | ☽ | Benefic* | Female | Water | Mind, emotions, mother, public |
| **Mars** | मंगल (Mangala) | ♂ | Malefic | Male | Fire | Energy, courage, siblings, property |
| **Mercury** | बुध (Budha) | ☿ | Neutral** | Neutral | Earth | Intellect, speech, trade, communication |
| **Jupiter** | गुरु (Guru) | ♃ | Benefic | Male | Ether | Wisdom, expansion, children, dharma |
| **Venus** | शुक्र (Shukra) | ♀ | Benefic | Female | Water | Love, luxury, art, vehicles, pleasure |
| **Saturn** | शनि (Shani) | ♄ | Malefic | Neutral | Air | Discipline, karma, delays, servants |
| **Rahu** | राहु | ☊ | Malefic | — | Smoke | Obsession, illusion, foreign, technology |
| **Ketu** | केतु | ☋ | Malefic | — | Fire | Liberation, detachment, spirituality, past life |

\* Moon is benefic when waxing (Shukla Paksha), malefic when waning (Krishna Paksha).
\** Mercury takes the nature of planets it associates with.

### Rahu and Ketu — The Lunar Nodes

These are not physical bodies. They are the two points where the Moon's orbit intersects the ecliptic (Earth's orbital plane).

- **Rahu** (North Node) = where the Moon crosses from south to north. Represents worldly desire, amplification, obsession.
- **Ketu** (South Node) = where the Moon crosses from north to south. Represents spirituality, detachment, past mastery.
- They are always exactly 180° apart.
- They move **retrograde** (backward through the zodiac) completing one cycle in ~18.6 years.

### Planetary Speeds (Average Daily Motion)

| Planet | Speed | Full Zodiac Cycle |
|--------|-------|-------------------|
| Moon | ~13°10'/day | ~27.3 days |
| Mercury | ~1°23'/day | ~88 days |
| Venus | ~1°12'/day | ~225 days |
| Sun | ~1°/day | ~365 days |
| Mars | ~0°31'/day | ~1.88 years |
| Jupiter | ~0°05'/day | ~11.86 years |
| Saturn | ~0°02'/day | ~29.46 years |
| Rahu/Ketu | ~0°03'/day (retro) | ~18.6 years |

### Retrograde Motion (Vakri)

When a planet appears to move backward from Earth's perspective (due to orbital mechanics), it is **retrograde**.

- Sun and Moon never go retrograde.
- Rahu and Ketu are always retrograde (by convention).
- Other planets go retrograde periodically.

**Effect:** A retrograde planet is considered **stronger** in Vedic astrology (opposite to Western). It gives internalized, intensified energy. A retrograde planet also behaves somewhat like it is in the previous sign.

### Combust (Asta)

When a planet is too close to the Sun (by longitude), it becomes **combust** — weakened because the Sun's light overwhelms it.

| Planet | Combustion Range |
|--------|-----------------|
| Moon | < 12° from Sun |
| Mars | < 17° |
| Mercury | < 14° (12° if retrograde) |
| Jupiter | < 11° |
| Venus | < 10° (8° if retrograde) |
| Saturn | < 15° |

**Code implication:** Check angular distance between each planet and Sun. If within range, flag as combust and reduce strength score.

---

## 5. The 12 Bhavas (Houses)

Houses are the 12 sectors of the sky, mapped from the Lagna. Each house governs specific life domains.

### House Significations

| House | Sanskrit | Name | Core Domain | Detailed Significations |
|-------|----------|------|-------------|------------------------|
| **1** | Tanu | Self | Body, personality | Physical appearance, health, temperament, overall life direction |
| **2** | Dhana | Wealth | Money, speech | Family wealth, food habits, speech quality, right eye, early education |
| **3** | Sahaja | Siblings | Courage, skills | Brothers/sisters, short travels, hands, communication, initiative |
| **4** | Sukha | Happiness | Home, mother | Property, vehicles, mother, education, inner peace, land |
| **5** | Putra | Children | Intelligence | Children, creativity, speculation, romance, past-life merit (purva punya) |
| **6** | Ripu | Enemies | Conflict, disease | Debts, diseases, enemies, litigation, service, daily work |
| **7** | Yuvati | Spouse | Partnership | Marriage, business partners, public dealings, foreign residence |
| **8** | Randhra | Transformation | Hidden things | Death, longevity, inheritance, occult, sudden events, insurance |
| **9** | Dharma | Fortune | Beliefs, luck | Father, guru, religion, philosophy, long journeys, higher education |
| **10** | Karma | Career | Action, status | Profession, reputation, authority, government, public standing |
| **11** | Labha | Gains | Income, networks | Profits, elder siblings, friends, large organizations, fulfilled desires |
| **12** | Vyaya | Loss | Expenditure | Foreign lands, spirituality, hospitals, prisons, moksha, bed pleasures |

### House Groupings

These groupings are critical for evaluation. A planet's house placement immediately tells you its functional flavor.

#### By Life Quality (Trines and Angles)

| Group | Houses | Sanskrit | Nature |
|-------|--------|----------|--------|
| **Kendra** (Angles) | 1, 4, 7, 10 | केन्द्र | Strength, stability, action. Planets here are powerful. Vishnu sthanas. |
| **Trikona** (Trines) | 1, 5, 9 | त्रिकोण | Fortune, dharma, merit. Most auspicious houses. Lakshmi sthanas. |
| **Upachaya** (Growth) | 3, 6, 10, 11 | उपचय | Improve over time. Malefics do well here. |
| **Dusthana** (Difficult) | 6, 8, 12 | दुःस्थान | Obstacles, suffering, loss. Planets here are weakened for worldly results. |
| **Maraka** (Killer) | 2, 7 | मारक | Can indicate health crises in certain dasha periods. |

#### By Domain

| Group | Houses | Domain |
|-------|--------|--------|
| **Dharma** (Purpose) | 1, 5, 9 | Life purpose, merit, wisdom |
| **Artha** (Wealth) | 2, 6, 10 | Material resources, work |
| **Kama** (Desire) | 3, 7, 11 | Desires, relationships, gains |
| **Moksha** (Liberation) | 4, 8, 12 | Inner life, transformation, freedom |

### House Lordship

The planet that **rules** the sign occupying a house becomes the **lord** of that house. House lords carry the significations of their house wherever they sit.

Example (Aries Lagna):
- House 1 = Aries → Lord = Mars
- House 2 = Taurus → Lord = Venus
- House 4 = Cancer → Lord = Moon
- House 9 = Sagittarius → Lord = Jupiter
- House 10 = Capricorn → Lord = Saturn

**This is critical:** The 1st lord (lagna lord) represents YOU. Where it sits, what aspects it, what dasha runs — all describe your life trajectory.

### Functional Benefics and Malefics

A planet's natural benefic/malefic status changes based on which houses it rules FOR YOUR SPECIFIC LAGNA. This is one of the most important concepts.

**For Aries Lagna (Nitin's chart):**

| Planet | Rules Houses | Functional Nature | Reason |
|--------|-------------|-------------------|--------|
| Mars | 1, 8 | Benefic (Lagna lord) | 1st lord always benefits the self |
| Venus | 2, 7 | Maraka (neutral-negative) | Rules two maraka houses |
| Mercury | 3, 6 | Malefic | Rules dusthana (6) and upachaya (3) |
| Moon | 4 | Benefic | Kendra lord |
| Sun | 5 | Strong benefic | Trikona lord |
| Jupiter | 9, 12 | Benefic | 9th lord (great trikona) despite 12th |
| Saturn | 10, 11 | Neutral-Malefic | Kendra lord but also 11th (badhaka for chara lagna) |
| Rahu | Acts like Saturn | Context-dependent | Takes on the role of its sign lord and conjunct planets |
| Ketu | Acts like Mars | Context-dependent | Takes on the role of its sign lord and conjunct planets |

---

## 6. Lagna — The Anchor

### What Lagna Actually Is

Lagna is the exact degree of the zodiac rising on the eastern horizon at the moment of birth, at the birth location.

**Calculation requires:**
1. Date and time of birth (converted to UTC/sidereal time)
2. Geographic coordinates (latitude, longitude)
3. Ayanamsa correction (tropical → sidereal)

The Lagna changes sign roughly every 2 hours (since the entire zodiac rises in ~24 hours). This is why birth time accuracy is critical.

### Lagna Degree vs Lagna Sign

- **Lagna sign** = the rashi (e.g., Aries) — determines house cusps in whole-sign system
- **Lagna degree** = the exact degree within that sign (e.g., 14°22' Aries) — matters for bhava chalit (house cusp-based) chart and for precision

### House Systems in Vedic Astrology

| System | Method | Usage |
|--------|--------|-------|
| **Whole Sign** (Rashi-based) | Lagna sign = 1st house, next sign = 2nd, etc. | Most traditional, what we use |
| **Bhava Chalit** (Equal House) | Lagna degree is mid-point of 1st house, equal 30° houses | Used for house-level analysis |
| **Sripati** | Midpoint between two bhava madhyas | Less common |
| **KP (Placidus-based)** | Unequal houses based on time | Used in KP system only |

**For this project:** We use **Whole Sign** as the primary system (already implemented in `bhava.py`). Bhava Chalit can be added as a secondary view.

---

## 7. The 27 Nakshatras (Lunar Mansions)

This is where Vedic astrology gets its precision. The zodiac is divided into 27 segments of 13°20' each, called Nakshatras.

### Why Nakshatras Matter
- Each nakshatra has a ruling planet → this drives the **Vimshottari Dasha** system
- Nakshatras give much finer personality/behavioral readings than signs alone
- Two people with Moon in Aries but different nakshatras will have very different dashas and temperaments

### Complete Nakshatra Table

| # | Nakshatra | Degrees | Ruler | Sign(s) | Deity | Nature |
|---|-----------|---------|-------|---------|-------|--------|
| 1 | **Ashwini** | 0°00'–13°20' Ari | Ketu | Aries | Ashwini Kumaras | Swift, healing |
| 2 | **Bharani** | 13°20'–26°40' Ari | Venus | Aries | Yama | Restraint, transformation |
| 3 | **Krittika** | 26°40' Ari–10°00' Tau | Sun | Aries/Taurus | Agni | Sharp, purifying |
| 4 | **Rohini** | 10°00'–23°20' Tau | Moon | Taurus | Brahma | Creative, fertile |
| 5 | **Mrigashira** | 23°20' Tau–6°40' Gem | Mars | Taurus/Gemini | Soma | Searching, curious |
| 6 | **Ardra** | 6°40'–20°00' Gem | Rahu | Gemini | Rudra | Stormy, intellectual |
| 7 | **Punarvasu** | 20°00' Gem–3°20' Can | Jupiter | Gemini/Cancer | Aditi | Renewal, return |
| 8 | **Pushya** | 3°20'–16°40' Can | Saturn | Cancer | Brihaspati | Nourishing, best nakshatra |
| 9 | **Ashlesha** | 16°40'–30°00' Can | Mercury | Cancer | Nagas | Clinging, mystical |
| 10 | **Magha** | 0°00'–13°20' Leo | Ketu | Leo | Pitris | Authority, ancestry |
| 11 | **Purva Phalguni** | 13°20'–26°40' Leo | Venus | Leo | Bhaga | Pleasure, creativity |
| 12 | **Uttara Phalguni** | 26°40' Leo–10°00' Vir | Sun | Leo/Virgo | Aryaman | Contracts, patronage |
| 13 | **Hasta** | 10°00'–23°20' Vir | Moon | Virgo | Savitar | Skill, craftsmanship |
| 14 | **Chitra** | 23°20' Vir–6°40' Lib | Mars | Virgo/Libra | Vishwakarma | Brilliance, creation |
| 15 | **Swati** | 6°40'–20°00' Lib | Rahu | Libra | Vayu | Independence, trade |
| 16 | **Vishakha** | 20°00' Lib–3°20' Sco | Jupiter | Libra/Scorpio | Indra-Agni | Determination, purpose |
| 17 | **Anuradha** | 3°20'–16°40' Sco | Saturn | Scorpio | Mitra | Devotion, friendship |
| 18 | **Jyeshtha** | 16°40'–30°00' Sco | Mercury | Scorpio | Indra | Seniority, protection |
| 19 | **Mula** | 0°00'–13°20' Sag | Ketu | Sagittarius | Nirriti | Root, destruction/creation |
| 20 | **Purva Ashada** | 13°20'–26°40' Sag | Venus | Sagittarius | Apas | Invincibility, purification |
| 21 | **Uttara Ashada** | 26°40' Sag–10°00' Cap | Sun | Sagittarius/Capricorn | Vishvadevas | Final victory, universal |
| 22 | **Shravana** | 10°00'–23°20' Cap | Moon | Capricorn | Vishnu | Learning, listening |
| 23 | **Dhanishta** | 23°20' Cap–6°40' Aqu | Mars | Capricorn/Aquarius | Vasus | Wealth, rhythm |
| 24 | **Shatabhisha** | 6°40'–20°00' Aqu | Rahu | Aquarius | Varuna | Healing, secrecy |
| 25 | **Purva Bhadrapada** | 20°00' Aqu–3°20' Pis | Jupiter | Aquarius/Pisces | Aja Ekapad | Scorching, transformation |
| 26 | **Uttara Bhadrapada** | 3°20'–16°40' Pis | Saturn | Pisces | Ahir Budhnya | Depth, wisdom |
| 27 | **Revati** | 16°40'–30°00' Pis | Mercury | Pisces | Pushan | Nurturing, journey's end |

### Nakshatra Padas (Quarters)

Each nakshatra is further divided into 4 **padas** (quarters) of 3°20' each.

- Total: 27 nakshatras × 4 padas = 108 padas
- Each pada maps to a sign in the Navamsa (D-9) chart
- The pada determines the Navamsa sign of a planet

### Nakshatra → Dasha Ruler Mapping

This is the key link between nakshatras and timing:

| Ruler | Nakshatras | Dasha Period (years) |
|-------|-----------|---------------------|
| **Ketu** | Ashwini, Magha, Mula | 7 |
| **Venus** | Bharani, Purva Phalguni, Purva Ashada | 20 |
| **Sun** | Krittika, Uttara Phalguni, Uttara Ashada | 6 |
| **Moon** | Rohini, Hasta, Shravana | 10 |
| **Mars** | Mrigashira, Chitra, Dhanishta | 7 |
| **Rahu** | Ardra, Swati, Shatabhisha | 18 |
| **Jupiter** | Punarvasu, Vishakha, Purva Bhadrapada | 16 |
| **Saturn** | Pushya, Anuradha, Uttara Bhadrapada | 19 |
| **Mercury** | Ashlesha, Jyeshtha, Revati | 17 |

**Total: 120 years** (the Vimshottari cycle)

### Computing Nakshatra from Longitude

```
nakshatra_index = floor(sidereal_longitude / (360/27))
                = floor(sidereal_longitude / 13.3333)

pada = floor((sidereal_longitude % 13.3333) / 3.3333) + 1
```

---

## 8. Planetary Dignity — Strength and Weakness

A planet's strength depends heavily on which sign it occupies. This is the dignity system.

### Dignity Levels (Strongest → Weakest)

| Level | Sanskrit | Description | Strength Multiplier |
|-------|----------|-------------|-------------------|
| **Exaltation** | Uccha | Peak power, planet at its best | Highest |
| **Moolatrikona** | Moolatrikona | "Root triplicity" — near-exaltation strength | Very High |
| **Own Sign** | Swakshetra | Planet in the sign it rules — comfortable, natural | High |
| **Friendly Sign** | Mitrastha | In a friend's sign — reasonably comfortable | Medium-High |
| **Neutral Sign** | Samastha | Neither friend nor enemy — average | Medium |
| **Enemy Sign** | Shatrustha | In an enemy's sign — uncomfortable | Low |
| **Debilitation** | Neecha | Weakest possible, planet at its worst | Lowest |

### Exaltation & Debilitation Table

| Planet | Exaltation Sign | Exact Degree | Debilitation Sign | Exact Degree |
|--------|----------------|-------------|-------------------|-------------|
| **Sun** | Aries | 10° | Libra | 10° |
| **Moon** | Taurus | 3° | Scorpio | 3° |
| **Mars** | Capricorn | 28° | Cancer | 28° |
| **Mercury** | Virgo | 15° | Pisces | 15° |
| **Jupiter** | Cancer | 5° | Capricorn | 5° |
| **Venus** | Pisces | 27° | Virgo | 27° |
| **Saturn** | Libra | 20° | Aries | 20° |
| **Rahu** | Taurus* | — | Scorpio* | — |
| **Ketu** | Scorpio* | — | Taurus* | — |

\* Rahu/Ketu exaltation is debated. Some texts say Gemini/Sagittarius.

### Moolatrikona Signs

| Planet | Moolatrikona Sign | Degrees |
|--------|------------------|---------|
| Sun | Leo | 0°–20° |
| Moon | Taurus | 3°–30° |
| Mars | Aries | 0°–12° |
| Mercury | Virgo | 15°–20° |
| Jupiter | Sagittarius | 0°–10° |
| Venus | Libra | 0°–15° |
| Saturn | Aquarius | 0°–20° |

### Own Signs

| Planet | Own Sign(s) |
|--------|------------|
| Sun | Leo |
| Moon | Cancer |
| Mars | Aries, Scorpio |
| Mercury | Gemini, Virgo |
| Jupiter | Sagittarius, Pisces |
| Venus | Taurus, Libra |
| Saturn | Capricorn, Aquarius |

### Neecha Bhanga Raja Yoga (Cancellation of Debilitation)

A debilitated planet can have its weakness cancelled (and become powerful) under specific conditions:
1. The lord of the debilitation sign is in a kendra from Lagna or Moon
2. The planet that gets exalted in the debilitation sign is in a kendra from Lagna or Moon
3. The debilitated planet is conjunct or aspected by the lord of its debilitation sign
4. The debilitated planet is in its exaltation in the Navamsa (D-9) chart

**Code implication:** Each planet needs a `dignity` field computed from its sign, and optionally a `neecha_bhanga` boolean check.

---

## 9. Planetary Relationships

### Natural Relationships (Naisargika Sambandha)

These are permanent, chart-independent relationships.

| Planet | Friends | Neutral | Enemies |
|--------|---------|---------|---------|
| **Sun** | Moon, Mars, Jupiter | Mercury | Venus, Saturn, Rahu, Ketu |
| **Moon** | Sun, Mercury | Mars, Jupiter, Venus, Saturn | Rahu, Ketu |
| **Mars** | Sun, Moon, Jupiter | Venus, Saturn | Mercury, Rahu, Ketu |
| **Mercury** | Sun, Venus | Mars, Jupiter, Saturn | Moon, Rahu, Ketu |
| **Jupiter** | Sun, Moon, Mars | Saturn | Mercury, Venus, Rahu, Ketu |
| **Venus** | Mercury, Saturn | Mars, Jupiter | Sun, Moon, Rahu, Ketu |
| **Saturn** | Mercury, Venus | Jupiter | Sun, Moon, Mars, Rahu, Ketu |
| **Rahu** | Mercury, Venus, Saturn | Jupiter | Sun, Moon, Mars |
| **Ketu** | Mars, Jupiter | Mercury, Venus, Saturn | Sun, Moon |

### Temporal Relationships (Tatkalika Sambandha)

These are chart-specific — based on actual positions:
- **Temporal friend:** Planet in 2nd, 3rd, 4th, 10th, 11th, or 12th house from another
- **Temporal enemy:** Planet in 1st, 5th, 6th, 7th, 8th, or 9th house from another

### Compound Relationship (Panchadha Sambandha)

Combine natural + temporal:

| Natural | Temporal | Compound Result |
|---------|----------|----------------|
| Friend | Friend | **Best Friend** (Adhi Mitra) |
| Friend | Enemy | **Neutral** (Sama) |
| Neutral | Friend | **Friend** (Mitra) |
| Neutral | Enemy | **Enemy** (Shatru) |
| Enemy | Friend | **Neutral** (Sama) |
| Enemy | Enemy | **Bitter Enemy** (Adhi Shatru) |

**Code implication:** For each pair of planets, compute both natural and temporal relationship, then derive compound. This feeds into strength calculations and interpretation.

---

## 10. Aspects (Drishti)

In Vedic astrology, aspects work differently from Western astrology.

### Standard Aspect

**Every planet aspects the 7th house from itself** (the house directly opposite, 180°).

### Special Aspects (Visheshadrishti)

Only Mars, Jupiter, and Saturn have additional aspects:

| Planet | Aspects Houses | Reasoning |
|--------|---------------|-----------|
| **Mars** | 4th, 7th, 8th from itself | Aggressive forward and backward glance |
| **Jupiter** | 5th, 7th, 9th from itself | Wisdom aspects — trines + opposition |
| **Saturn** | 3rd, 7th, 10th from itself | Pressure aspects — effort + opposition + authority |

### Rahu and Ketu Aspects

Debated among traditions:
- Some say Rahu/Ketu aspect 5th, 7th, 9th (like Jupiter)
- Some say only 7th
- Some say no aspects at all

**For this project:** We'll use 5th, 7th, 9th for Rahu/Ketu (the more widely accepted view).

### Aspect Strength

Full aspects vs partial aspects (used in some traditions):

| Aspect | Strength |
|--------|----------|
| 7th house | Full (100%) |
| 3rd, 10th (Saturn) | Full (100%) |
| 4th, 8th (Mars) | Full (100%) |
| 5th, 9th (Jupiter) | Full (100%) |

In Vedic astrology, aspects are generally considered full-strength (unlike Western's orb-based system).

### Aspect Computation

```
aspected_house = (planet_house + aspect_distance - 1) % 12 + 1
```

Already implemented in `aspects.py`. We need to extend it for Rahu/Ketu.

---

## 11. Shadbala — Six-Fold Strength

Shadbala is the comprehensive strength calculation system. It quantifies how powerful each planet is in a given chart.

### The Six Components

| # | Bala | Sanskrit | What it measures | Weight |
|---|------|----------|-----------------|--------|
| 1 | **Sthana Bala** | स्थान बल | Positional strength (sign, house, dignity) | High |
| 2 | **Dig Bala** | दिग् बल | Directional strength (planet in its preferred direction) | Medium |
| 3 | **Kala Bala** | काल बल | Temporal strength (day/night, hora, year lord, etc.) | Medium |
| 4 | **Chesta Bala** | चेष्टा बल | Motional strength (retrograde, speed, direction) | Medium |
| 5 | **Naisargika Bala** | नैसर्गिक बल | Natural strength (inherent planetary power) | Low |
| 6 | **Drik Bala** | दृक् बल | Aspectual strength (aspects received from benefics/malefics) | Medium |

### Sthana Bala (Positional) — Subcomponents

| Component | Measures |
|-----------|----------|
| **Uccha Bala** | How close to exaltation degree (max = at exact exaltation, min = at debilitation) |
| **Saptavargaja Bala** | Dignity across 7 divisional charts |
| **Ojha-Yugma Bala** | Odd/even sign placement compatibility |
| **Kendradi Bala** | Bonus for being in kendra, trikona, etc. |
| **Drekkana Bala** | Decanate-based strength |

### Dig Bala (Directional Strength)

Each planet has maximum strength in a specific house:

| Planet | Strongest House (Dig Bala) | Direction |
|--------|--------------------------|-----------|
| Sun | 10th | South (Zenith) |
| Mars | 10th | South |
| Jupiter | 1st | East |
| Mercury | 1st | East |
| Moon | 4th | North (Nadir) |
| Venus | 4th | North |
| Saturn | 7th | West |

### Naisargika Bala (Natural Strength)

Fixed hierarchy, does not change:

```
Sun (60) > Moon (51.4) > Venus (42.8) > Jupiter (34.3) > Mercury (25.7) > Mars (17.1) > Saturn (8.6)
```

### Minimum Required Shadbala (in Rupas)

| Planet | Minimum Shadbala (Rupas) |
|--------|------------------------|
| Sun | 5.0 |
| Moon | 6.0 |
| Mars | 5.0 |
| Mercury | 7.0 |
| Jupiter | 6.5 |
| Venus | 5.5 |
| Saturn | 5.0 |

A planet meeting or exceeding its minimum is considered functionally strong.

**Code implication:** Shadbala is the most complex computation in the system. We can implement it incrementally — start with Uccha Bala and Dig Bala (simplest), add others over time. This replaces the simple `strength` float currently in the database.

---

## 12. Yogas — Planetary Combinations

Yogas are specific planetary configurations that produce defined results. There are hundreds; here are the most important ones.

### Pancha Mahapurusha Yogas (5 Great Person Yogas)

These form when Mars, Mercury, Jupiter, Venus, or Saturn is in its own sign or exaltation AND in a kendra (1, 4, 7, 10) from Lagna.

| Yoga | Planet | Condition | Result |
|------|--------|-----------|--------|
| **Ruchaka** | Mars | Own/exalted in kendra | Courage, leadership, military |
| **Bhadra** | Mercury | Own/exalted in kendra | Intelligence, communication, trade |
| **Hamsa** | Jupiter | Own/exalted in kendra | Wisdom, dharma, teaching |
| **Malavya** | Venus | Own/exalted in kendra | Luxury, art, beauty, comfort |
| **Shasha** | Saturn | Own/exalted in kendra | Power, discipline, authority |

**Nitin's chart check:** Mars is in Aries (own sign) in House 1 (kendra) → **Ruchaka Yoga present!**

### Wealth Yogas (Dhana Yogas)

| Yoga | Formation | Result |
|------|-----------|--------|
| **Dhana Yoga** | Lord of 2nd + Lord of 11th connected (conjunction, aspect, or exchange) | Wealth accumulation |
| **Lakshmi Yoga** | Lord of 9th strong + in kendra/trikona | Fortune, prosperity |
| **Gajakesari** | Jupiter in kendra from Moon | Fame, intelligence, wealth |

### Raja Yogas (Power Yogas)

The most important category. Formed by connection between:
- **Kendra lords** (1, 4, 7, 10) and **Trikona lords** (1, 5, 9)

Any conjunction, mutual aspect, or sign exchange between a kendra lord and a trikona lord creates a Raja Yoga.

**Nitin's chart:** Jupiter (lord of 9) in House 9, Moon (lord of 4) in House 9 — conjunction of kendra lord and trikona lord → **Raja Yoga present.**

### Negative Yogas

| Yoga | Formation | Result |
|------|-----------|--------|
| **Kemadruma** | No planets in 2nd or 12th from Moon | Poverty, loneliness (many cancellations exist) |
| **Grahan Yoga** | Sun/Moon conjunct Rahu/Ketu | Eclipse yoga — obscured luminaries |
| **Shakata Yoga** | Jupiter in 6th, 8th, or 12th from Moon | Fluctuating fortune |
| **Daridra Yoga** | Lord of 11th in dusthana | Blocked gains |

### Yoga Detection Algorithm

```
for each known yoga:
    check planet positions, signs, houses, lordships
    check aspects and conjunctions
    if all conditions met:
        flag yoga as present
        assign score/weight
```

**Code implication:** The `rules/` directory is where yogas get implemented. Each yoga is a `Rule` subclass with `applies()` and `score()` methods.

---

## 13. Vimshottari Dasha — The Timing Engine

This is the single most powerful predictive tool in Vedic astrology. It answers: **WHEN will things happen?**

### How It Works

1. At birth, the Moon is in a specific **nakshatra**
2. That nakshatra's ruler becomes the first **Mahadasha** lord
3. Based on how far the Moon has traveled through that nakshatra, the remaining balance of the first dasha is calculated
4. After that, dashas follow the fixed sequence for the remaining life

### Dasha Sequence and Durations

| # | Planet | Duration (years) |
|---|--------|-----------------|
| 1 | Ketu | 7 |
| 2 | Venus | 20 |
| 3 | Sun | 6 |
| 4 | Moon | 10 |
| 5 | Mars | 7 |
| 6 | Rahu | 18 |
| 7 | Jupiter | 16 |
| 8 | Saturn | 19 |
| 9 | Mercury | 17 |

**Total = 120 years** (one full cycle)

### Dasha Levels (Hierarchy)

| Level | Sanskrit | Duration | Governs |
|-------|----------|----------|---------|
| **Mahadasha** | महादशा | Years (6–20) | Major life theme |
| **Antardasha** (Bhukti) | अन्तर्दशा | Months (varies) | Sub-theme within Mahadasha |
| **Pratyantardasha** | प्रत्यन्तर्दशा | Weeks | Finer sub-theme |
| **Sookshma** | सूक्ष्म | Days | Daily trigger |
| **Prana** | प्राण | Hours | Finest level |

For practical purposes, **Mahadasha + Antardasha** is sufficient for most predictions. Pratyantardasha adds weekly-level precision.

### Computing Dasha Balance at Birth

```
Moon's nakshatra = determine from Moon's sidereal longitude
Nakshatra ruler = lookup from table
Total dasha years of that ruler = Y

Moon's position within nakshatra = M° (0° to 13°20')
Fraction elapsed = M / 13.3333
Remaining fraction = 1 - fraction_elapsed
Remaining years of first Mahadasha = Y × remaining_fraction

Start date of first Mahadasha = birth_date
End date = birth_date + remaining_years
```

Then subsequent dashas follow the sequence.

### Antardasha Computation

Within each Mahadasha of planet X (duration D years):
- The first Antardasha lord = X itself
- Then follow the sequence starting from X
- Duration of each Antardasha = (Mahadasha lord's years × Antardasha lord's years) / 120

Example: Saturn Mahadasha (19 years)
- Saturn-Saturn: (19 × 19) / 120 = 3.008 years
- Saturn-Mercury: (19 × 17) / 120 = 2.692 years
- Saturn-Ketu: (19 × 7) / 120 = 1.108 years
- Saturn-Venus: (19 × 20) / 120 = 3.167 years
- ... and so on

### Dasha Interpretation Framework

The result of a dasha period depends on:

1. **The dasha lord's natal position** — sign, house, dignity, strength
2. **What houses the dasha lord rules** — its functional role
3. **What yogas the dasha lord participates in** — activates those yogas
4. **Aspects on the dasha lord** — modifies the results
5. **The dasha lord's relationship with the Lagna lord** — friend/enemy
6. **Transit of the dasha lord during its period** — current-sky activation

**Nitin's current situation:**
- Mahadasha: Saturn (2020–2039)
- Saturn in Aquarius (own sign), House 11 → very strong, gains-focused
- Saturn rules Houses 10 and 11 for Aries Lagna → career + gains
- This is a period of structured building, institutional achievement, large-scale projects

---

## 14. Transits (Gochar)

Transits are the real-time positions of planets in the current sky, overlaid on the natal chart.

### How Transits Work

- Calculate current sidereal positions of all 9 planets
- See which natal houses they are transiting through
- Evaluate their interaction with natal planet positions

### Key Transit Rules

| Transit Planet | Key Houses from Moon Sign | Effect |
|---------------|--------------------------|--------|
| **Jupiter** | Good in 2, 5, 7, 9, 11 from Moon | Expansion, opportunity |
| **Saturn** | Good in 3, 6, 11 from Moon | Discipline paying off |
| **Saturn** | Difficult in 1, 4, 7, 8, 10, 12 from Moon | Pressure, delays |
| **Rahu** | Amplifies the house it transits | Obsession, unconventional events |
| **Mars** | Short-term trigger (stays ~45 days/sign) | Energy, conflict, action |

### Sade Sati (Saturn's 7.5-Year Transit)

When Saturn transits through the 12th, 1st, and 2nd houses from natal Moon sign, it creates **Sade Sati** — a challenging ~7.5-year period.

- **Phase 1** (12th from Moon): Mental stress, expenses, sleep issues (~2.5 years)
- **Phase 2** (over Moon): Peak pressure, identity restructuring (~2.5 years)
- **Phase 3** (2nd from Moon): Financial pressure, family stress (~2.5 years)

**Nitin's Moon is in Sagittarius.**
- Saturn was in Capricorn (2nd from Moon) → Phase 3 of Sade Sati (around 2020-2023)
- Saturn in Aquarius (3rd from Moon) → Sade Sati ended. Favorable transit now.
- Saturn moves to Pisces (4th from Moon) around 2025-2028 → moderate

### Transit Speed and Impact Duration

| Planet | Time per Sign | Impact Character |
|--------|--------------|-----------------|
| Saturn | ~2.5 years | Deep structural changes |
| Jupiter | ~1 year | Opportunities, growth |
| Rahu/Ketu | ~1.5 years | Obsession/detachment themes |
| Mars | ~1.5 months | Action triggers |
| Sun | ~1 month | Authority, spotlight |
| Mercury | ~1 month | Communication, deals |
| Venus | ~1 month | Relationships, finance |
| Moon | ~2.25 days | Mood, daily fluctuations |

### Double Transit Theory (Gochar Vichar)

A major event happens ONLY when **both Jupiter and Saturn** aspect or transit a particular house simultaneously. This is one of the most reliable predictive techniques.

Example: For marriage (7th house matters), Jupiter AND Saturn must both influence the 7th house from Lagna (by transit or aspect) during the right Dasha.

---

## 15. Ashtakavarga — Transit Scoring

Ashtakavarga is a numerical scoring system that quantifies how favorable a transit is. It removes subjectivity from transit interpretation.

### How It Works

1. For each of the 7 planets (Sun through Saturn) + Lagna, create a grid of 12 signs
2. Each planet contributes **benefic points (bindus)** to certain signs based on its natal position
3. Sum the bindus for each sign across all contributors

### Bindu Contribution Table

Each planet has a fixed set of houses (from its own position) where it contributes a bindu:

| Planet | Contributes bindus from its position to houses # |
|--------|--------------------------------------------------|
| Sun | 1, 2, 4, 7, 8, 9, 10, 11 |
| Moon | 3, 6, 7, 8, 10, 11 |
| Mars | 1, 2, 4, 7, 8, 10, 11 |
| Mercury | 1, 2, 4, 7, 8, 9, 10, 11 |
| Jupiter | 1, 2, 3, 4, 7, 8, 10, 11 |
| Venus | 1, 2, 3, 4, 5, 8, 9, 11 |
| Saturn | 3, 5, 6, 11 |
| Lagna | 3, 6, 10, 11 |

### Sarvashtakavarga (SAV)

The combined score across all planets for each sign. Maximum possible = 56 per sign (8 contributors × 7 max bindus each, though actual distribution varies).

**Interpretation:**
- Sign with **28+** bindus: Very favorable when transited
- Sign with **25–27**: Average
- Sign with **below 25**: Unfavorable when transited

### Bhinnaashtakavarga (BAV)

Individual planet's score in each sign. Maximum = 8 per sign.

- Planet transiting a sign where its BAV score ≥ 4: **favorable**
- Planet transiting a sign where its BAV score ≤ 3: **unfavorable**

### Code Implication

Ashtakavarga can be computed once (natal-dependent) and cached. Then for any transit, just look up the BAV score:

```python
def is_transit_favorable(planet, transit_sign, bav_table):
    return bav_table[planet][transit_sign] >= 4
```

This is extremely valuable for the daily todo/avoid feature and for financial predictions.

---

## 16. Divisional Charts (Vargas)

The natal chart (D-1, Rashi chart) is just the first of many charts derived from the same birth data.

### Key Divisional Charts

| Chart | Division | Each Segment | Purpose |
|-------|----------|-------------|---------|
| **D-1** (Rashi) | 1 (30°) | Full sign | Overall life |
| **D-2** (Hora) | 2 (15°) | Half sign | Wealth |
| **D-3** (Drekkana) | 3 (10°) | Third of sign | Siblings, courage |
| **D-4** (Chaturthamsa) | 4 (7°30') | Quarter sign | Property, fortune |
| **D-7** (Saptamsa) | 7 (4°17') | Seventh of sign | Children |
| **D-9** (Navamsa) | 9 (3°20') | Ninth of sign | **Marriage, soul, dharma** |
| **D-10** (Dasamsa) | 10 (3°) | Tenth of sign | **Career** |
| **D-12** (Dwadasamsa) | 12 (2°30') | Twelfth of sign | Parents |
| **D-16** (Shodasamsa) | 16 (1°52.5') | — | Vehicles, comforts |
| **D-20** (Vimsamsa) | 20 (1°30') | — | Spirituality |
| **D-24** (Chaturvimsamsa) | 24 (1°15') | — | Education |
| **D-27** (Bhamsa) | 27 (1°6.67') | — | Physical strength |
| **D-30** (Trimsamsa) | 30 (1°) | — | Misfortune, evils |
| **D-40** (Khavedamsa) | 40 | — | Auspicious effects |
| **D-45** (Akshavedamsa) | 45 | — | General indications |
| **D-60** (Shashtyamsa) | 60 (0°30') | — | **Past life karma** (finest) |

### Most Important Divisional Charts

1. **D-1 (Rashi)** — The main chart. Everything starts here.
2. **D-9 (Navamsa)** — The "soul chart." Considered almost as important as D-1. Shows:
   - Marriage quality and spouse
   - How planets truly deliver results
   - A planet strong in D-1 but weak in D-9 underdelivers
   - A planet weak in D-1 but strong in D-9 has hidden strength
3. **D-10 (Dasamsa)** — Career chart. Shows professional life in detail.

### Navamsa Computation

For a planet at sidereal longitude L:
```
sign_number = floor(L / 30) + 1          # 1-12
degree_in_sign = L % 30
navamsa_number = floor(degree_in_sign / 3.3333) + 1   # 1-9

# Navamsa sign depends on element of natal sign:
# Fire signs start from Aries
# Earth signs start from Capricorn
# Air signs start from Libra
# Water signs start from Cancer

navamsa_start = {Fire: 0, Earth: 9, Air: 6, Water: 3}
navamsa_sign = (navamsa_start[element] + navamsa_number - 1) % 12 + 1
```

### Vargottama

When a planet occupies the **same sign** in both D-1 and D-9, it is called **Vargottama** — exceptionally strong. This is like being in "own sign" across dimensions.

---

## 17. Mundane & Financial Astrology

This is the branch most relevant to trading. Mundane astrology deals with world events, markets, and collective trends rather than individual charts.

### Planetary Significations in Markets

| Planet | Market Domain | Sector Affinity | When Strong | When Weak |
|--------|-------------|-----------------|-------------|-----------|
| **Sun** | Government policy, leadership changes | PSU, Government, Gold | Stability, authority | Policy chaos |
| **Moon** | Public sentiment, consumer mood | FMCG, Silver, Consumption | Bullish retail | Panic, emotional selling |
| **Mars** | Aggression, energy, conflict | Defense, Metals, Energy, Real Estate | Rallies, breakouts | Wars, sharp corrections |
| **Mercury** | Communication, trade, data | IT, FinTech, Telecom | Tech rallies, deal flow | Miscommunication, data errors |
| **Jupiter** | Expansion, banking, credit | Banking, Insurance, Education | Credit expansion, bull runs | Over-leverage, corrections |
| **Venus** | Luxury, comfort, aesthetics | Auto, Media, Luxury, Hotels | Consumer spending up | Austerity |
| **Saturn** | Contraction, discipline, structure | Infrastructure, Oil & Gas, Utilities | Slow steady gains | Recession, tightening |
| **Rahu** | Speculation, disruption, tech | Technology, Crypto, Foreign | Volatile rallies, bubbles | Crashes, fraud exposed |
| **Ketu** | Detachment, uncertainty | Pharma, Research, Spiritual | Defensive plays work | Confusion, no direction |

### Commodity-Planet Mapping

| Commodity | Ruling Planet(s) | Secondary |
|-----------|-----------------|-----------|
| **Gold** | Sun, Jupiter | Saturn (storage of value) |
| **Silver** | Moon | Venus |
| **Crude Oil** | Saturn, Mars | Rahu (volatility) |
| **Copper** | Venus, Mars | — |
| **Natural Gas** | Rahu, Saturn | Mars (energy) |
| **Agricultural** | Moon, Venus | Mercury (trade) |

### Index-Planet Correlations

| Index | Primary Planets | Reasoning |
|-------|----------------|-----------|
| **Nifty 50** | Jupiter (banking heavy), Saturn (infrastructure) | Large-cap stability |
| **Bank Nifty** | Jupiter, Mercury | Banking + trade |
| **Nifty IT** | Mercury, Rahu | Technology + disruption |
| **Nifty Metal** | Mars, Saturn | Energy + structure |
| **S&P 500** | Jupiter, Rahu | Expansion + speculation |
| **VIX** | Rahu, Ketu, Mars | Fear + uncertainty + aggression |

### Transit-Based Market Signals

| Event | Typical Market Effect |
|-------|---------------------|
| Jupiter enters new sign | Sector rotation (favors new sign's sectors) |
| Saturn enters new sign | ~2.5-year structural theme change |
| Saturn-Jupiter conjunction | ~20-year economic cycle reset |
| Mars conjunct Rahu | Sudden volatility spike, crashes possible |
| Mercury retrograde | Communication errors, deal failures, IT glitches |
| Eclipse (Sun/Moon + Rahu/Ketu) | Uncertainty spike, 2-week volatility window |
| Venus combust | Luxury/consumption weakness |

### Planetary War (Graha Yuddha)

When two planets are within 1° of each other, they are in "planetary war." The planet with lower latitude wins. The loser is weakened.

**Market effect:** Conflicting signals in the sectors ruled by the warring planets. Increased volatility in their domains.

### Rashi of India (National Chart)

India's independence chart (15 Aug 1947, 00:00 IST, Delhi) is often used as the "natal chart" of the market:
- Lagna: Taurus
- Moon: Cancer
- Transits to this chart affect macro market movements

### How to Build a Financial Astro Score

```
daily_score = 0

for each planet P in transit:
    sign_S = current_transit_sign(P)

    # 1. Ashtakavarga score of P in S
    score += bav[P][S] - 4  # positive if favorable

    # 2. Dignity of P in S
    score += dignity_score(P, S)  # exalted=+2, own=+1, debil=-2

    # 3. Aspect interactions
    for each natal planet N:
        if P aspects N or conjuncts N:
            score += relationship_score(P, N) * aspect_strength

    # 4. Dasha context (for personal chart)
    if P == current_dasha_lord:
        score *= 1.5  # dasha lord's transit matters more

    # 5. Special events
    if eclipse_today(): score -= 2
    if mercury_retrograde(): score -= 1

return normalize(score, -10, +10)
```

---

## 18. Putting It All Together — The Engine Model

### The Complete Jyotish Analysis Pipeline

```
INPUT:
  - Date, Time, Place of birth
  - Current date/time (for transits)

STEP 1: COMPUTE NATAL CHART
  ├── Convert birth time → UTC → Local Sidereal Time
  ├── Get tropical positions (ephemeris)
  ├── Subtract ayanamsa → sidereal positions
  ├── Compute Lagna degree & sign
  ├── Assign houses (whole sign from Lagna)
  ├── Place planets in houses
  ├── Compute nakshatras for each planet
  └── Generate divisional charts (D-9, D-10 at minimum)

STEP 2: ANALYZE NATAL CHART
  ├── Compute planetary dignity (exalt/own/debil/etc.)
  ├── Compute planetary relationships (natural + temporal)
  ├── Compute aspects given and received
  ├── Compute Shadbala (six-fold strength)
  ├── Compute Ashtakavarga tables
  ├── Identify Yogas
  └── Determine functional benefic/malefic for Lagna

STEP 3: COMPUTE TIMING
  ├── Calculate Vimshottari Dasha balance at birth
  ├── Generate full Dasha timeline (Maha + Antar + Pratyantar)
  ├── Determine current active Dasha at any given date
  └── Evaluate Dasha lord's natal strength & house lordship

STEP 4: COMPUTE TRANSITS (for any target date)
  ├── Get current sidereal positions of all planets
  ├── Overlay on natal houses
  ├── Check Ashtakavarga scores for transit signs
  ├── Check special events (retrograde, combust, eclipse, war)
  ├── Check Sade Sati status
  └── Apply double transit theory

STEP 5: SYNTHESIZE
  ├── Combine natal strength + dasha context + transit triggers
  ├── Generate scores per life domain (career, wealth, health, etc.)
  ├── For financial: generate regime (direction, volatility, sectors)
  └── Output: daily recommendations, alerts, regime parameters
```

### Data Flow Diagram

```
Birth Data ──→ Ephemeris ──→ Sidereal Positions ──→ Natal Chart
                                                        │
                              ┌──────────────────────────┤
                              │                          │
                         Dignity/Strength          House Placement
                              │                          │
                              ├── Shadbala               ├── Yogas
                              ├── Ashtakavarga           ├── Aspects
                              │                          ├── Lordships
                              │                          │
                    Moon Nakshatra ──→ Dasha Timeline
                                          │
Current Date ──→ Ephemeris ──→ Transit Positions
                                    │
                                    ├── Transit over natal houses
                                    ├── Ashtakavarga lookup
                                    ├── Special events check
                                    │
                    Dasha Context + Transit Scores ──→ DAILY OUTPUT
                                                        │
                              ┌──────────────────────────┤
                              │                          │
                    Personal Guidance          Financial Regime
                    (todo / avoid)            (direction, vol, sectors)
```

---

## 19. Nitin's Chart — Worked Example

### Birth Data
- **Date:** 7 March 1975
- **Time:** 9:45 AM IST (4:15 AM UTC)
- **Place:** Durg, India (21.19°N, 81.28°E)
- **Ayanamsa:** Lahiri (Chitrapaksha)

### Natal Chart Summary

| Planet | Sign | House | Dignity | Notes |
|--------|------|-------|---------|-------|
| Sun | Aquarius | 11 | Own sign of dispositor (Saturn) | Core identity = systems + groups |
| Moon | Sagittarius | 9 | Friendly (Jupiter rules Sag) | Mind in dharma house |
| Mars | Aries | 1 | **Own sign** | Lagna lord in Lagna — very powerful (**Ruchaka Yoga**) |
| Mercury | Aquarius | 11 | Friendly | Analytical, tech-oriented mind in gains house |
| Jupiter | Sagittarius | 9 | **Own sign (Moolatrikona)** | Dharma lord in dharma house — exceptional |
| Venus | Capricorn | 10 | Neutral | Career house — disciplined approach to relationships |
| Saturn | Aquarius | 11 | **Own sign (Moolatrikona)** | 10th & 11th lord in 11th — career-gains axis strong |
| Rahu | Cancer | 4 | — | Home life unconventional, mother's influence amplified |
| Ketu | Capricorn | 10 | — | Detachment from status/career per se |

### Key Yogas Present

| Yoga | Formation | Implication |
|------|-----------|-------------|
| **Ruchaka Yoga** | Mars in own sign in 1st house (kendra) | Leadership, courage, physical vitality |
| **Raja Yoga** | Moon (lord 4, kendra) + Jupiter (lord 9, trikona) in conjunction in House 9 | Power through wisdom and fortune |
| **Gajakesari Yoga** | Jupiter in kendra from Moon (1st from Moon = same house) | Intelligence, fame, lasting achievements |
| **Strong 11th house** | Sun + Mercury + Saturn in 11th | Gains from networks, large-scale systems, technology |

### Current Dasha Timeline

| Level | Planet | Period | Interpretation |
|-------|--------|--------|---------------|
| Mahadasha | Saturn | 2020–2039 | Long-term building, institutional work, discipline pays off |
| (Antardasha level needs computation from exact Moon nakshatra position) |

### House Lordship Table (Aries Lagna)

| House | Sign | Lord | Lord's Position | Interpretation |
|-------|------|------|----------------|---------------|
| 1 | Aries | Mars | House 1 (own sign) | Self-driven, powerful personality |
| 2 | Taurus | Venus | House 10 | Wealth through career |
| 3 | Gemini | Mercury | House 11 | Skills monetized through networks |
| 4 | Cancer | Moon | House 9 | Home connected to philosophy/travel |
| 5 | Leo | Sun | House 11 | Intelligence directed toward large gains |
| 6 | Virgo | Mercury | House 11 | Enemies/obstacles overcome through networks |
| 7 | Libra | Venus | House 10 | Partnership tied to career |
| 8 | Scorpio | Mars | House 1 | Transformation through self-initiative |
| 9 | Sagittarius | Jupiter | House 9 | Fortune lord in fortune house — very auspicious |
| 10 | Capricorn | Saturn | House 11 | Career lord in gains house — career produces income |
| 11 | Aquarius | Saturn | House 11 | Gains lord in gains house — self-fulfilling |
| 12 | Pisces | Jupiter | House 9 | Expenses on dharma, travel, higher learning |

---

## 20. Buildable Modules Map

Each section above maps to a concrete module we can build. Here's the priority order:

### Phase 1 — Foundation (Ephemeris + Core Computation)
| Module | What it does | Maps to Section |
|--------|-------------|-----------------|
| `ephemeris.py` | Swiss Ephemeris wrapper → tropical positions | §2 |
| `ayanamsa.py` | Tropical → Sidereal conversion | §2 |
| `nakshatra.py` | Longitude → Nakshatra + Pada | §7 |
| `dignity.py` | Compute exaltation/debilitation/own/friend/enemy | §8 |
| `relationships.py` | Natural + Temporal planetary relationships | §9 |

### Phase 2 — Chart Analysis
| Module | What it does | Maps to Section |
|--------|-------------|-----------------|
| `aspects.py` (extend) | Full aspect table including Rahu/Ketu | §10 |
| `yogas.py` | Detect Mahapurusha, Raja, Dhana, negative yogas | §12 |
| `house_lords.py` | Compute lordships, functional benefic/malefic | §5 |
| `navamsa.py` | Compute D-9 chart, check Vargottama | §16 |
| `dasamsa.py` | Compute D-10 chart | §16 |

### Phase 3 — Timing Engine
| Module | What it does | Maps to Section |
|--------|-------------|-----------------|
| `dasha_calc.py` | Full Vimshottari computation (Maha + Antar + Pratyantar) | §13 |
| `transit.py` | Current planetary positions + natal overlay | §14 |
| `ashtakavarga.py` | BAV + SAV computation and transit scoring | §15 |
| `sade_sati.py` | Saturn transit relative to Moon sign | §14 |

### Phase 4 — Scoring & Output
| Module | What it does | Maps to Section |
|--------|-------------|-----------------|
| `shadbala.py` | Six-fold strength (incremental) | §11 |
| `daily_score.py` | Combine dasha + transit + ashtakavarga → daily score | §18 |
| `astro_regime.py` (extend) | Financial regime from combined scores | §17 |
| `recommendations.py` | Daily todo/avoid generation | §18 |

### Phase 5 — Financial Module
| Module | What it does | Maps to Section |
|--------|-------------|-----------------|
| `commodity_signals.py` | Planet-commodity mapping + transit scoring | §17 |
| `index_signals.py` | Planet-index mapping + transit scoring | §17 |
| `market_events.py` | Eclipse, retrograde, planetary war detection | §17 |
| `volatility_model.py` | Rahu/Ketu/Mars transit → VIX-like score | §17 |

---

## Glossary

| Term | Meaning |
|------|---------|
| **Ayanamsa** | Angular difference between tropical and sidereal zodiacs |
| **Bhava** | House |
| **Dasha** | Planetary period (timing system) |
| **Drishti** | Aspect (planetary gaze) |
| **Dusthana** | Difficult houses (6, 8, 12) |
| **Gochar** | Transit |
| **Graha** | Planet |
| **Kendra** | Angular houses (1, 4, 7, 10) |
| **Lagna** | Ascendant |
| **Nakshatra** | Lunar mansion (27 divisions of zodiac) |
| **Navamsa** | 9th divisional chart (D-9) |
| **Rashi** | Sign |
| **Shadbala** | Six-fold planetary strength |
| **Trikona** | Trine houses (1, 5, 9) |
| **Uccha** | Exaltation |
| **Neecha** | Debilitation |
| **Vakri** | Retrograde |
| **Yoga** | Planetary combination producing specific results |
| **Varga** | Divisional chart |

---

*This document is the reference for building AstroLogic. Each module we build should be traceable to a section here.*
