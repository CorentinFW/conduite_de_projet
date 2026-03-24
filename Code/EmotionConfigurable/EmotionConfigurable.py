#!/usr/bin/env python3

# Exemple d'exécution (depuis la racine du dépôt):
# python3 Code/EmotionConfigurable/EmotionConfigurable.py --oracle-config Emotion/EmotionProjetBase/oracle_config_emotiondamage.json --response-mapping Emotion/EmotionProjetBase/response_mapping_emotiondamage.json

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple


class MappingConfigError(Exception):
    """Raised when the response mapping file is invalid."""


class OracleClientError(Exception):
    """Raised when oracle invocation or parsing fails."""


@dataclass(frozen=True)
class EmotionPrediction:
    emotion_id: str
    label: Optional[str]
    confidence: float


@dataclass(frozen=True)
class InferenceResult:
    primary_emotion_id: str
    emotions: Tuple[EmotionPrediction, ...]
    overall_confidence: float


@dataclass(frozen=True)
class ConfidenceThresholds:
    low_lt: float
    medium_lt: float


@dataclass(frozen=True)
class ResponseRule:
    emotion_id: str
    confidence_level: str
    response_text: str


@dataclass(frozen=True)
class ResponseDefaults:
    emotion_id: str
    confidence_level: str
    empty_input_response: str


@dataclass(frozen=True)
class ResponseMapping:
    schema_version: str
    confidence_levels: Tuple[str, ...]
    confidence_thresholds: ConfidenceThresholds
    responses: Dict[str, Dict[str, str]]
    defaults: ResponseDefaults

    def get_rule(self, emotion_id: str, confidence_level: str) -> Optional[ResponseRule]:
        by_emotion = self.responses.get(emotion_id)
        if by_emotion is None:
            return None
        response_text = by_emotion.get(confidence_level)
        if response_text is None:
            return None
        return ResponseRule(
            emotion_id=emotion_id,
            confidence_level=confidence_level,
            response_text=response_text,
        )


def _require_object(value: Any, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise MappingConfigError(f"Field '{field_name}' must be a JSON object.")
    return value


def _require_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MappingConfigError(f"Field '{field_name}' must be a non-empty string.")
    return value


def _require_float(value: Any, field_name: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise MappingConfigError(f"Field '{field_name}' must be numeric.") from exc


def _require_string_list(value: Any, field_name: str) -> Tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise MappingConfigError(f"Field '{field_name}' must be a non-empty list of strings.")

    labels: List[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise MappingConfigError(f"Field '{field_name}[{index}]' must be a non-empty string.")
        labels.append(item.strip())

    if len(set(labels)) != len(labels):
        raise MappingConfigError(f"Field '{field_name}' contains duplicate values.")

    return tuple(labels)


def load_response_mapping(path: str) -> ResponseMapping:
    if not path:
        raise MappingConfigError("Response mapping path is empty.")

    mapping_path = Path(path)
    if not mapping_path.exists():
        raise MappingConfigError(f"Response mapping file not found: {path}")

    try:
        with mapping_path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
    except json.JSONDecodeError as exc:
        raise MappingConfigError(f"Invalid JSON in response mapping: {exc}") from exc
    except OSError as exc:
        raise MappingConfigError(f"Unable to read response mapping file: {exc}") from exc

    root = _require_object(raw, "root")
    schema_version = _require_string(root.get("schema_version"), "schema_version")
    confidence_levels = _require_string_list(root.get("confidence_levels"), "confidence_levels")

    thresholds_raw = _require_object(root.get("confidence_thresholds"), "confidence_thresholds")
    low_lt = _require_float(thresholds_raw.get("low_lt"), "confidence_thresholds.low_lt")
    medium_lt = _require_float(thresholds_raw.get("medium_lt"), "confidence_thresholds.medium_lt")
    if not low_lt < medium_lt:
        raise MappingConfigError("Expected confidence_thresholds.low_lt < confidence_thresholds.medium_lt.")

    if set(confidence_levels) != {"low", "medium", "high"}:
        raise MappingConfigError("Field 'confidence_levels' must contain exactly: low, medium, high.")

    responses_raw = _require_object(root.get("responses"), "responses")
    responses: Dict[str, Dict[str, str]] = {}
    for emotion_id, per_level in responses_raw.items():
        if not isinstance(emotion_id, str) or not emotion_id.strip():
            raise MappingConfigError("All keys in 'responses' must be non-empty emotion IDs.")
        level_map = _require_object(per_level, f"responses.{emotion_id}")

        validated_level_map: Dict[str, str] = {}
        for level in confidence_levels:
            text = _require_string(level_map.get(level), f"responses.{emotion_id}.{level}")
            validated_level_map[level] = text

        responses[emotion_id.strip()] = validated_level_map

    defaults_raw = _require_object(root.get("defaults"), "defaults")
    defaults = ResponseDefaults(
        emotion_id=_require_string(defaults_raw.get("emotion_id"), "defaults.emotion_id"),
        confidence_level=_require_string(
            defaults_raw.get("confidence_level"),
            "defaults.confidence_level",
        ),
        empty_input_response=_require_string(
            defaults_raw.get("empty_input_response"),
            "defaults.empty_input_response",
        ),
    )

    if defaults.confidence_level not in confidence_levels:
        raise MappingConfigError("Field 'defaults.confidence_level' must be present in 'confidence_levels'.")

    if defaults.emotion_id not in responses:
        raise MappingConfigError("Field 'defaults.emotion_id' must exist in 'responses'.")

    thresholds = ConfidenceThresholds(low_lt=low_lt, medium_lt=medium_lt)
    return ResponseMapping(
        schema_version=schema_version,
        confidence_levels=confidence_levels,
        confidence_thresholds=thresholds,
        responses=responses,
        defaults=defaults,
    )


class OracleClient:
    def __init__(self, oracle_config_path: str):
        if not oracle_config_path:
            raise OracleClientError("Oracle config path is empty.")

        self._oracle_config_path = oracle_config_path
        self._oracle_script_path = (Path(__file__).resolve().parents[1] / "oracle.py").resolve()
        if not self._oracle_script_path.exists():
            raise OracleClientError(f"Oracle script not found: {self._oracle_script_path}")

    def infer(self, text: str) -> InferenceResult:
        command = [
            sys.executable,
            str(self._oracle_script_path),
            "--config",
            self._oracle_config_path,
            "--text",
            text,
        ]
        try:
            completed = subprocess.run(
                command,
                check=False,
                text=True,
                capture_output=True,
            )
        except OSError as exc:
            raise OracleClientError(f"Unable to execute oracle: {exc}") from exc

        if completed.returncode != 0:
            stderr_text = (completed.stderr or "").strip() or "Oracle failed without stderr details."
            raise OracleClientError(stderr_text)

        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise OracleClientError(f"Oracle output is not valid JSON: {exc}") from exc

        return self._parse_inference_payload(payload)

    def _parse_inference_payload(self, payload: Any) -> InferenceResult:
        if not isinstance(payload, dict):
            raise OracleClientError("Oracle output root must be a JSON object.")

        result_raw = payload.get("result")
        if not isinstance(result_raw, dict):
            raise OracleClientError("Oracle output missing object: result.")

        primary_emotion_id = result_raw.get("primary_emotion_id")
        if not isinstance(primary_emotion_id, str) or not primary_emotion_id.strip():
            raise OracleClientError("Oracle output has invalid result.primary_emotion_id.")

        overall_confidence_raw = result_raw.get("overall_confidence")
        try:
            overall_confidence = float(overall_confidence_raw)
        except (TypeError, ValueError) as exc:
            raise OracleClientError("Oracle output has invalid result.overall_confidence.") from exc

        emotions_raw = result_raw.get("emotions")
        if not isinstance(emotions_raw, list) or not emotions_raw:
            raise OracleClientError("Oracle output has invalid result.emotions.")

        emotions: List[EmotionPrediction] = []
        for index, item in enumerate(emotions_raw):
            if not isinstance(item, dict):
                raise OracleClientError(f"Oracle output emotion at index {index} must be an object.")

            emotion_id = item.get("id")
            if not isinstance(emotion_id, str) or not emotion_id.strip():
                raise OracleClientError(f"Oracle output emotion at index {index} has invalid id.")

            label = item.get("label")
            if label is not None and not isinstance(label, str):
                raise OracleClientError(f"Oracle output emotion at index {index} has invalid label.")

            confidence_raw = item.get("confidence")
            try:
                confidence = float(confidence_raw)
            except (TypeError, ValueError) as exc:
                raise OracleClientError(
                    f"Oracle output emotion at index {index} has invalid confidence."
                ) from exc

            emotions.append(
                EmotionPrediction(
                    emotion_id=emotion_id,
                    label=label,
                    confidence=confidence,
                )
            )

        return InferenceResult(
            primary_emotion_id=primary_emotion_id,
            emotions=tuple(emotions),
            overall_confidence=overall_confidence,
        )


def confidence_to_level(confidence: float, thresholds: ConfidenceThresholds) -> str:
    if confidence < thresholds.low_lt:
        return "low"
    if confidence < thresholds.medium_lt:
        return "medium"
    return "high"


class ResponseSelector:
    def __init__(self, mapping: ResponseMapping):
        self._mapping = mapping

    def select(self, emotion_id: str, confidence_level: str) -> str:
        direct_rule = self._mapping.get_rule(emotion_id, confidence_level)
        if direct_rule is not None:
            return direct_rule.response_text

        fallback_rule = self._mapping.get_rule(
            self._mapping.defaults.emotion_id,
            self._mapping.defaults.confidence_level,
        )
        if fallback_rule is not None:
            return fallback_rule.response_text

        return self._mapping.defaults.empty_input_response


def run_dialogue_loop(oracle_client: OracleClient, mapping: ResponseMapping) -> int:
    selector = ResponseSelector(mapping)

    while True:
        try:
            user_text = input("Vous: ")
        except EOFError:
            print()
            return 0
        except KeyboardInterrupt:
            print()
            return 0

        if not user_text.strip():
            print(mapping.defaults.empty_input_response)
            continue

        try:
            inference = oracle_client.infer(user_text)
        except OracleClientError as exc:
            print(f"Erreur oracle: {exc}", file=sys.stderr)
            return 2

        confidence_level = confidence_to_level(
            inference.overall_confidence,
            mapping.confidence_thresholds,
        )
        response_text = selector.select(inference.primary_emotion_id, confidence_level)
        print(response_text)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="EmotionConfigurable (oracle + mapping)")
    parser.add_argument(
        "--oracle-config",
        required=True,
        help="Path to oracle JSON configuration file.",
    )
    parser.add_argument(
        "--response-mapping",
        required=True,
        help="Path to response mapping JSON file.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    try:
        mapping = load_response_mapping(args.response_mapping)
    except MappingConfigError as exc:
        print(f"Erreur de configuration mapping: {exc}", file=sys.stderr)
        return 2

    try:
        oracle_client = OracleClient(args.oracle_config)
        oracle_client.infer("")
    except OracleClientError as exc:
        print(f"Erreur de configuration oracle: {exc}", file=sys.stderr)
        return 2

    return run_dialogue_loop(oracle_client, mapping)


if __name__ == "__main__":
    raise SystemExit(main())
