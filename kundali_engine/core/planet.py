from dataclasses import dataclass

@dataclass
class PlanetPosition:
    name: str
    longitude: float
    sign: str
    house: int
    nakshatra: str
    retrograde: bool = False
