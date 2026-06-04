from dataclasses import dataclass


@dataclass
class Medication:
    name: str
    dose: str = ""
    frequency: str = ""
    duration: str = ""
