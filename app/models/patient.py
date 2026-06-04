from dataclasses import dataclass, field
from typing import Literal


AgeGroup = Literal["Child", "Adult", "Elderly"]


@dataclass
class Patient:
    age_group: AgeGroup
    pregnant: bool = False
    breastfeeding: bool = False
    symptoms: list[str] = field(default_factory=list)
