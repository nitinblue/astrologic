import sqlite3
from datetime import date
from dataclasses import dataclass

@dataclass
class AstroRegime:
    directional_bias: str
    volatility_bias: str
    risk_multiplier: float
    allowed_strategies: list
    favored_sectors: list
    explanation: list

STRATEGY_CLASSES = {
    "bullish_defined": ["bull_put_spread", "call_debit_spread"],
    "bearish_defined": ["bear_call_spread", "put_debit_spread"],
    "neutral_income": ["iron_condor", "short_strangle"],
    "long_vol": ["calendar", "diagonal"]
}

PLANET_SECTOR_MAP = {
    "Sun": ["Government", "PSU", "Leadership"],
    "Moon": ["FMCG", "Consumption"],
    "Mars": ["Defense", "Metals", "Energy"],
    "Mercury": ["IT", "FinTech", "Trading"],
    "Jupiter": ["Banking", "Insurance"],
    "Venus": ["Luxury", "Auto", "Media"],
    "Saturn": ["Infrastructure", "Utilities", "Oil & Gas"],
    "Rahu": ["Technology", "Speculation", "Crypto"],
    "Ketu": ["Pharma", "Research"]
}

def compute_astro_regime(db="astro.db", person_id=1) -> AstroRegime:
    conn = sqlite3.connect(db)
    cur = conn.cursor()

    # Active Mahadasha
    cur.execute("""
        SELECT planet FROM dasha
        WHERE person_id=? AND level='maha'
    """, (person_id,))
    dasha_planet = cur.fetchone()[0]

    # Natal placement
    cur.execute("""
        SELECT house, strength FROM natal_planet
        WHERE person_id=? AND planet=?
    """, (person_id, dasha_planet))
    house, strength = cur.fetchone()

    explanation = []
    risk = 1.0
    directional = "neutral"
    vol = "neutral"

    # Dasha-based logic
    if dasha_planet in ("Jupiter", "Mars"):
        directional = "bullish"
        risk = 1.2
        explanation.append(f"{dasha_planet} dasha favors risk-on")

    if dasha_planet == "Saturn":
        risk = 0.7
        vol = "contract"
        explanation.append("Saturn dasha → capital protection")

    if dasha_planet == "Rahu":
        vol = "expand"
        explanation.append("Rahu dasha → convexity & speculation")

    # House-based modifier
    if house in (6, 8, 12):
        risk *= 0.7
        explanation.append("Dasha planet in dusthana → reduce exposure")

    # Strategy filter
    if directional == "bullish":
        strategies = STRATEGY_CLASSES["bullish_defined"]
    elif directional == "bearish":
        strategies = STRATEGY_CLASSES["bearish_defined"]
    elif vol == "expand":
        strategies = STRATEGY_CLASSES["long_vol"]
    else:
        strategies = STRATEGY_CLASSES["neutral_income"]

    # Sector bias
    sectors = PLANET_SECTOR_MAP.get(dasha_planet, [])

    conn.close()

    return AstroRegime(
        directional_bias=directional,
        volatility_bias=vol,
        risk_multiplier=round(risk * strength, 2),
        allowed_strategies=strategies,
        favored_sectors=sectors,
        explanation=explanation
    )
