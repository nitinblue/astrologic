from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class BirthData:
    date_time_utc: datetime
    latitude: float
    longitude: float
    ayanamsa: str = "lahiri"
