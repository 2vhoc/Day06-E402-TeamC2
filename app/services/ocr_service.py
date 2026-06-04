from abc import ABC, abstractmethod
from typing import Any


class OCRService(ABC):
    @abstractmethod
    def extract_prescription(
        self,
        image: bytes,
        mime_type: str = "image/jpeg",
    ) -> dict[str, Any]:
        pass
