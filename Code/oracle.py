#!/usr/bin/env python3

# Exemple d'usage portable (depuis le dossier CONDUITE_DE_PROJET):
# python3 Code/oracle.py --config example_oracle_config.json --text "Merci pour ton aide, mais je suis un peu stressé"
#
# Exemple d'usage portable (depuis n'importe quel dossier):
# cd /chemin/vers/CONDUITE_DE_PROJET && python3 Code/oracle.py --config example_oracle_config.json --text "Merci pour ton aide, mais je suis un peu stressé"

"""Heuristic emotion oracle with JSON-configurable scoring."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Sequence, Tuple


class ConfigError(Exception):
    """Raised when the oracle configuration is invalid."""


@dataclass(frozen=True)
class EmotionConfig:
    id: str
    label: str
    aliases: Tuple[str, ...]
    keywords: Tuple[str, ...]
    negations: Tuple[str, ...]
    weight: float


@dataclass(frozen=True)
class CalibrationConfig:
    base: float
    per_keyword_hit: float
    per_alias_hit: float
    ambiguity_penalty: float
    negation_penalty: float
    max_emotions: int


@dataclass(frozen=True)
class ConfidenceConfig:
    scale: str
    min_value: float
    max_value: float
    calibration: CalibrationConfig


@dataclass(frozen=True)
class BehaviorConfig:
    allow_multiple_emotions: bool
    unknown_emotion_id: str
    language_hint: str


@dataclass(frozen=True)
class OracleConfig:
    schema_version: str
    emotions: Tuple[EmotionConfig, ...]
    confidence: ConfidenceConfig
    behavior: BehaviorConfig


class ConfigLoader:
    """Loads and lightly validates oracle configuration from JSON."""

    @staticmethod
    def load(config_path: str) -> OracleConfig:
        if not config_path:
            raise ConfigError("Config path is empty.")
        if not os.path.exists(config_path):
            raise ConfigError(f"Config file not found: {config_path}")

        try:
            with open(config_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except json.JSONDecodeError as exc:
            raise ConfigError(f"Invalid JSON in config file: {exc}") from exc
        except OSError as exc:
            raise ConfigError(f"Unable to read config file: {exc}") from exc

        if not isinstance(data, dict):
            raise ConfigError("Config root must be a JSON object.")

        schema_version = str(data.get("schema_version", "1.0"))

        raw_emotions = data.get("emotions")
        if not isinstance(raw_emotions, list) or not raw_emotions:
            raise ConfigError("Config field 'emotions' must be a non-empty list.")

        emotions: List[EmotionConfig] = []
        for index, raw_item in enumerate(raw_emotions):
            if not isinstance(raw_item, dict):
                raise ConfigError(f"Emotion at index {index} must be an object.")

            emotion_id = str(raw_item.get("id", "")).strip()
            label = str(raw_item.get("label", emotion_id)).strip()
            if not emotion_id:
                raise ConfigError(f"Emotion at index {index} has missing or empty 'id'.")
            if not label:
                label = emotion_id

            aliases = ConfigLoader._as_string_tuple(raw_item.get("aliases", []))
            keywords = ConfigLoader._as_string_tuple(raw_item.get("keywords", []))
            negations = ConfigLoader._as_string_tuple(raw_item.get("negations", []))

            weight_value = raw_item.get("weight", 1.0)
            try:
                weight = float(weight_value)
            except (TypeError, ValueError) as exc:
                raise ConfigError(
                    f"Emotion '{emotion_id}' has invalid 'weight': {weight_value}"
                ) from exc

            emotions.append(
                EmotionConfig(
                    id=emotion_id,
                    label=label,
                    aliases=aliases,
                    keywords=keywords,
                    negations=negations,
                    weight=weight,
                )
            )

        confidence_raw = data.get("confidence")
        if not isinstance(confidence_raw, dict):
            raise ConfigError("Config field 'confidence' must be an object.")

        scale = str(confidence_raw.get("scale", "0_1"))

        min_raw = confidence_raw.get("min", 0.0)
        max_raw = confidence_raw.get("max", 1.0)
        try:
            min_value = float(min_raw)
            max_value = float(max_raw)
        except (TypeError, ValueError) as exc:
            raise ConfigError("Config fields 'confidence.min/max' must be numeric.") from exc

        if min_value > max_value:
            raise ConfigError("Config field 'confidence.min' must be <= 'confidence.max'.")

        calibration_raw = confidence_raw.get("calibration")
        if not isinstance(calibration_raw, dict):
            raise ConfigError("Config field 'confidence.calibration' must be an object.")

        calibration = CalibrationConfig(
            base=ConfigLoader._as_float(calibration_raw.get("base", 0.2), "calibration.base"),
            per_keyword_hit=ConfigLoader._as_float(
                calibration_raw.get("per_keyword_hit", 0.15),
                "calibration.per_keyword_hit",
            ),
            per_alias_hit=ConfigLoader._as_float(
                calibration_raw.get("per_alias_hit", 0.20),
                "calibration.per_alias_hit",
            ),
            ambiguity_penalty=ConfigLoader._as_float(
                calibration_raw.get("ambiguity_penalty", 0.25),
                "calibration.ambiguity_penalty",
            ),
            negation_penalty=ConfigLoader._as_float(
                calibration_raw.get("negation_penalty", 0.30),
                "calibration.negation_penalty",
            ),
            max_emotions=max(1, int(calibration_raw.get("max_emotions", 3))),
        )

        behavior_raw = data.get("behavior", {})
        if not isinstance(behavior_raw, dict):
            raise ConfigError("Config field 'behavior' must be an object.")

        behavior = BehaviorConfig(
            allow_multiple_emotions=bool(behavior_raw.get("allow_multiple_emotions", True)),
            unknown_emotion_id=str(behavior_raw.get("unknown_emotion_id", "unknown")) or "unknown",
            language_hint=str(behavior_raw.get("language_hint", "auto")) or "auto",
        )

        return OracleConfig(
            schema_version=schema_version,
            emotions=tuple(emotions),
            confidence=ConfidenceConfig(
                scale=scale,
                min_value=min_value,
                max_value=max_value,
                calibration=calibration,
            ),
            behavior=behavior,
        )

    @staticmethod
    def _as_string_tuple(value: Any) -> Tuple[str, ...]:
        if value is None:
            return tuple()
        if not isinstance(value, list):
            raise ConfigError("Aliases/keywords/negations must be lists of strings.")
        result: List[str] = []
        for item in value:
            text = str(item).strip().lower()
            if text:
                result.append(text)
        return tuple(result)

    @staticmethod
    def _as_float(value: Any, field_name: str) -> float:
        try:
            return float(value)
        except (TypeError, ValueError) as exc:
            raise ConfigError(f"Config field '{field_name}' must be numeric.") from exc


class TextNormalizer:
    """Normalizes text and performs naive negation checks."""

    _whitespace_re = re.compile(r"\s+")

    def normalize(self, text: str) -> str:
        lowered = str(text).lower().strip()
        return self._whitespace_re.sub(" ", lowered)

    def has_negation(self, normalized_text: str, negations: Sequence[str]) -> bool:
        if not normalized_text:
            return False
        for marker in negations:
            marker_clean = marker.strip().lower()
            if not marker_clean:
                continue
            if self._contains_phrase(normalized_text, marker_clean):
                return True
        return False

    @staticmethod
    def _contains_phrase(text: str, phrase: str) -> bool:
        if " " in phrase:
            pattern = r"(^|\W)" + re.escape(phrase) + r"($|\W)"
            return re.search(pattern, text, flags=re.IGNORECASE) is not None
        pattern = r"\b" + re.escape(phrase) + r"\b"
        return re.search(pattern, text, flags=re.IGNORECASE) is not None


class EmotionScorer:
    """Scores emotions based on keyword/alias hits and penalties."""

    def __init__(self, config: OracleConfig, normalizer: TextNormalizer):
        self._config = config
        self._normalizer = normalizer

    def score(self, normalized_text: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        calibration = self._config.confidence.calibration
        notes: List[str] = []
        scored: List[Dict[str, Any]] = []

        if not normalized_text:
            notes.append("empty_input")
            return [], notes

        for emotion in self._config.emotions:
            matched_keywords = self._match_terms(normalized_text, emotion.keywords)
            matched_aliases = self._match_terms(normalized_text, emotion.aliases)
            negation_detected = self._normalizer.has_negation(normalized_text, emotion.negations)

            hit_count = len(matched_keywords) + len(matched_aliases)
            if hit_count == 0:
                continue

            base_score = (
                calibration.base
                + len(matched_keywords) * calibration.per_keyword_hit
                + len(matched_aliases) * calibration.per_alias_hit
            )
            weighted_score = base_score * emotion.weight
            if negation_detected:
                weighted_score -= calibration.negation_penalty

            confidence = self._clamp(weighted_score)

            scored.append(
                {
                    "id": emotion.id,
                    "label": emotion.label,
                    "confidence": confidence,
                    "evidence": {
                        "matched_keywords": matched_keywords,
                        "matched_aliases": matched_aliases,
                        "negation_detected": negation_detected,
                    },
                }
            )

        if not scored:
            notes.append("no_emotion_detected")
            return [], notes

        positive_count = sum(1 for item in scored if item["confidence"] > self._config.confidence.min_value)
        if positive_count > 1:
            notes.append("ambiguous_emotions")
            for item in scored:
                item["confidence"] = self._clamp(item["confidence"] - calibration.ambiguity_penalty)

        if any(item["evidence"]["negation_detected"] for item in scored):
            notes.append("negation_detected")

        scored.sort(key=lambda item: (-item["confidence"], item["id"]))

        if not self._config.behavior.allow_multiple_emotions:
            scored = scored[:1]

        scored = scored[: calibration.max_emotions]

        return scored, notes

    def _match_terms(self, text: str, terms: Sequence[str]) -> List[str]:
        matches: List[str] = []
        seen: set[str] = set()
        for term in terms:
            token = term.strip().lower()
            if not token or token in seen:
                continue
            if TextNormalizer._contains_phrase(text, token):
                matches.append(token)
                seen.add(token)
        return matches

    def _clamp(self, value: float) -> float:
        min_value = self._config.confidence.min_value
        max_value = self._config.confidence.max_value
        return float(max(min_value, min(max_value, value)))


class Oracle:
    """Coordinates config loading, normalization, scoring, and output assembly."""

    ENGINE_NAME = "heuristic_v1"

    def __init__(self, config: OracleConfig, config_path: str):
        self._config = config
        self._config_path = config_path
        self._normalizer = TextNormalizer()
        self._scorer = EmotionScorer(config, self._normalizer)

    def infer(self, text: str) -> Dict[str, Any]:
        normalized_text = self._normalizer.normalize(text)

        emotions, notes = self._scorer.score(normalized_text)

        if not emotions:
            emotions = [self._unknown_emotion()]

        emotions.sort(key=lambda item: (-item["confidence"], item["id"]))

        overall_confidence = float(
            max(
                self._config.confidence.min_value,
                min(self._config.confidence.max_value, max(item["confidence"] for item in emotions)),
            )
        )

        timestamp_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

        result: Dict[str, Any] = {
            "input": {
                "text": text,
                "normalized_text": normalized_text,
            },
            "result": {
                "emotions": emotions,
                "primary_emotion_id": emotions[0]["id"],
                "overall_confidence": overall_confidence,
                "notes": notes,
            },
            "meta": {
                "schema_version": self._config.schema_version,
                "config_path": self._config_path,
                "timestamp_utc": timestamp_utc,
                "engine": self.ENGINE_NAME,
            },
        }

        return result

    def _unknown_emotion(self) -> Dict[str, Any]:
        unknown_id = self._config.behavior.unknown_emotion_id or "unknown"
        low_confidence = float(
            max(
                self._config.confidence.min_value,
                min(
                    self._config.confidence.max_value,
                    self._config.confidence.min_value
                    + (self._config.confidence.max_value - self._config.confidence.min_value) * 0.1,
                ),
            )
        )
        return {
            "id": unknown_id,
            "label": unknown_id,
            "confidence": low_confidence,
            "evidence": {
                "matched_keywords": [],
                "matched_aliases": [],
                "negation_detected": False,
            },
        }


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Heuristic emotion oracle")
    parser.add_argument("--config", required=True, help="Path to JSON configuration file")
    parser.add_argument("--text", help="Input text. If omitted, text is read from stdin.")
    parser.add_argument("--seed", type=int, help="Optional deterministic seed (accepted for API compatibility)")
    return parser


def _read_text_argument_or_stdin(text_arg: str | None) -> str:
    if text_arg is not None:
        return text_arg
    return sys.stdin.read()


def main() -> int:
    parser = build_argument_parser()
    args = parser.parse_args()

    if args.seed is not None:
        pass

    try:
        config = ConfigLoader.load(args.config)
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    text_input = _read_text_argument_or_stdin(args.text)

    oracle = Oracle(config=config, config_path=args.config)
    payload = oracle.infer(text_input)

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
