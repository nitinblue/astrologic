from dataclasses import dataclass

@dataclass(frozen=True)
class ZodiacSign:
    name: str
    element: str
    modality: str
    ruler: str
