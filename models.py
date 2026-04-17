from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Frame:
    """Generic frame object using slots as named fillers."""

    frame_id: str
    frame_type: str
    name: str
    slots: dict[str, Any] = field(default_factory=dict)

    def get_slot(self, slot_name: str, default: Any | None = None) -> Any:
        return self.slots.get(slot_name, default)

    def fill_slot(self, slot_name: str, value: Any) -> None:
        self.slots[slot_name] = value


@dataclass
class PatientProfile:
    symptoms: list[str]
    risk_factors: list[str] = field(default_factory=list)
    age: int | None = None
    duration_days: int | None = None
    vitals: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DiagnosisResult:
    disease_name: str
    confidence: float
    matched_symptoms: list[str]
    matched_risk_factors: list[str]
    missing_key_symptoms: list[str]
    supporting_tests: list[str]
    evidence_paths: list[str]
    explanation: str


@dataclass(frozen=True)
class DiagnosisReport:
    patient_frame: Frame
    top_diagnoses: list[DiagnosisResult]
    detected_red_flags: list[str]
    unknown_terms: list[str]
    graph_summary: dict[str, int]
