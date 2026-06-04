from abc import ABC, abstractmethod
from typing import Any


class DrugRepository(ABC):
    @abstractmethod
    def get_drug(self, name: str) -> dict[str, Any] | None:
        pass
