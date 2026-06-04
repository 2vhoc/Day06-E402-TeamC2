import json
import re
from pathlib import Path
from difflib import SequenceMatcher
from typing import Any
import unicodedata

from app.repositories.drug_repository import DrugRepository


class JsonDrugRepository(DrugRepository):
    FUZZY_MATCH_THRESHOLD = 0.82
    AMBIGUOUS_CANDIDATE_THRESHOLD = 0.76
    AMBIGUOUS_MATCH_SCORE_GAP = 0.04
    IGNORED_TOKENS = {
        "an",
        "cap",
        "capsule",
        "capsules",
        "coated",
        "film",
        "gio",
        "hop",
        "lan",
        "lo",
        "mcg",
        "mg",
        "ml",
        "ngay",
        "ong",
        "sang",
        "sau",
        "tab",
        "tablet",
        "tablets",
        "toi",
        "truoc",
        "uong",
        "vien",
        "x",
    }

    def __init__(self, data_path: str | Path | None = None) -> None:
        self.data_path = Path(data_path) if data_path else self._default_data_path()
        self._drugs = self._load_drugs()

    def get_drug(self, name: str) -> dict[str, Any] | None:
        normalized_name = self._normalize_for_lookup(name)
        if not normalized_name:
            return None

        exact_match = self._find_exact_match(normalized_name)
        if exact_match is not None:
            return exact_match

        contained_match = self._find_contained_match(normalized_name)
        if contained_match is not None:
            return contained_match

        return self._find_fuzzy_match(normalized_name)

    def _find_exact_match(self, normalized_name: str) -> dict[str, Any] | None:
        for drug in self._drugs:
            for search_name in self._drug_search_names(drug):
                if self._normalize_for_lookup(search_name) == normalized_name:
                    return drug

        return None

    def _find_contained_match(self, normalized_name: str) -> dict[str, Any] | None:
        padded_name = f" {normalized_name} "
        matches = []

        for drug in self._drugs:
            for search_name in self._drug_search_names(drug):
                normalized_drug_name = self._normalize_for_lookup(search_name)
                if not normalized_drug_name:
                    continue

                if f" {normalized_drug_name} " in padded_name:
                    matches.append(drug)
                    break

                if self._all_tokens_present(normalized_drug_name, normalized_name):
                    matches.append(drug)
                    break

        unique_matches = self._unique_drugs(matches)
        if not unique_matches:
            return None

        if len(unique_matches) > 1:
            return self._with_match_warning(
                drug=unique_matches[0],
                candidates=self._candidate_names(unique_matches[1:]),
            )

        return unique_matches[0]

    def _find_fuzzy_match(self, normalized_name: str) -> dict[str, Any] | None:
        scored_matches = []

        for drug in self._drugs:
            for search_name in self._drug_search_names(drug):
                normalized_drug_name = self._normalize_for_lookup(search_name)
                if not normalized_drug_name:
                    continue

                score = self._similarity_score(normalized_name, normalized_drug_name)
                scored_matches.append((score, drug))

        unique_scored_matches = self._unique_scored_drugs(scored_matches)
        if not unique_scored_matches:
            return None

        best_score, best_drug = unique_scored_matches[0]
        if best_score < self.FUZZY_MATCH_THRESHOLD:
            return None

        close_candidates = [
            drug
            for score, drug in unique_scored_matches[1:]
            if score >= self.AMBIGUOUS_CANDIDATE_THRESHOLD
            and best_score - score <= self.AMBIGUOUS_MATCH_SCORE_GAP
        ]
        if close_candidates:
            return self._with_match_warning(
                drug=best_drug,
                candidates=self._candidate_names(close_candidates),
            )

        return best_drug

    @classmethod
    def _similarity_score(cls, normalized_name: str, normalized_drug_name: str) -> float:
        scores = [
            SequenceMatcher(None, normalized_name, normalized_drug_name).ratio(),
        ]

        name_tokens = normalized_name.split()
        drug_tokens = normalized_drug_name.split()
        window_size = len(drug_tokens)
        if window_size == 0:
            return 0.0

        for index in range(0, len(name_tokens) - window_size + 1):
            window = " ".join(name_tokens[index : index + window_size])
            scores.append(SequenceMatcher(None, window, normalized_drug_name).ratio())

        if len(drug_tokens) == 1:
            for token in name_tokens:
                scores.append(SequenceMatcher(None, token, normalized_drug_name).ratio())

        return max(scores)

    @staticmethod
    def _all_tokens_present(normalized_drug_name: str, normalized_name: str) -> bool:
        drug_tokens = set(normalized_drug_name.split())
        name_tokens = set(normalized_name.split())

        return bool(drug_tokens) and drug_tokens.issubset(name_tokens)

    @classmethod
    def _drug_search_names(cls, drug: dict[str, Any]) -> list[str]:
        search_names = [str(drug.get("name", ""))]
        aliases = drug.get("aliases", [])

        if isinstance(aliases, list):
            search_names.extend(str(alias) for alias in aliases)

        drug_name = str(drug.get("name", ""))
        parenthetical_names = re.findall(r"\(([^)]+)\)", drug_name)
        search_names.extend(parenthetical_names)

        name_without_parentheses = re.sub(r"\([^)]*\)", " ", drug_name)
        search_names.append(name_without_parentheses)

        return cls._unique_search_names(search_names)

    @classmethod
    def _unique_search_names(cls, search_names: list[str]) -> list[str]:
        unique_names = []
        seen_names = set()
        for search_name in search_names:
            normalized_name = cls._normalize_for_lookup(search_name)
            if not normalized_name or normalized_name in seen_names:
                continue

            seen_names.add(normalized_name)
            unique_names.append(search_name)

        return unique_names

    @staticmethod
    def _unique_drugs(drugs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        unique_drugs = []
        seen_names = set()
        for drug in drugs:
            drug_name = str(drug.get("name", "")).casefold()
            if not drug_name or drug_name in seen_names:
                continue

            seen_names.add(drug_name)
            unique_drugs.append(drug)

        return unique_drugs

    @classmethod
    def _unique_scored_drugs(
        cls,
        scored_matches: list[tuple[float, dict[str, Any]]],
    ) -> list[tuple[float, dict[str, Any]]]:
        best_by_name: dict[str, tuple[float, dict[str, Any]]] = {}
        for score, drug in scored_matches:
            drug_name = str(drug.get("name", "")).casefold()
            if not drug_name:
                continue

            current_match = best_by_name.get(drug_name)
            if current_match is None or score > current_match[0]:
                best_by_name[drug_name] = (score, drug)

        return sorted(best_by_name.values(), key=lambda match: match[0], reverse=True)

    @staticmethod
    def _candidate_names(drugs: list[dict[str, Any]]) -> list[str]:
        return [str(drug.get("name", "")) for drug in drugs[:3] if str(drug.get("name", "")).strip()]

    @staticmethod
    def _with_match_warning(
        drug: dict[str, Any],
        candidates: list[str],
    ) -> dict[str, Any]:
        matched_drug = dict(drug)
        if not candidates:
            return matched_drug

        matched_drug["_match_candidates"] = candidates
        matched_drug["_match_warning"] = (
            "Tên thuốc OCR có thể bị nhầm với thuốc gần giống: "
            f"{', '.join(candidates)}. Vui lòng kiểm tra lại đơn thuốc."
        )
        return matched_drug

    @classmethod
    def _normalize_for_lookup(cls, text: str) -> str:
        normalized_text = "".join(
            character
            for character in unicodedata.normalize("NFD", str(text))
            if unicodedata.category(character) != "Mn"
        )
        normalized_text = normalized_text.replace("đ", "d").replace("Đ", "D").casefold()
        normalized_text = re.sub(r"[^a-z0-9]+", " ", normalized_text)

        tokens = []
        for token in normalized_text.split():
            if token.isdigit():
                continue
            if token in cls.IGNORED_TOKENS:
                continue
            if re.fullmatch(r"\d+[a-z]+", token):
                continue
            tokens.append(token)

        return " ".join(tokens)

    def _load_drugs(self) -> list[dict[str, Any]]:
        try:
            with self.data_path.open(encoding="utf-8") as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

        drugs = data.get("drugs", []) if isinstance(data, dict) else data
        if not isinstance(drugs, list):
            return []

        return [drug for drug in drugs if isinstance(drug, dict)]

    @staticmethod
    def _default_data_path() -> Path:
        return Path(__file__).resolve().parents[1] / "data" / "drugs.json"
