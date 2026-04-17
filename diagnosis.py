from __future__ import annotations

from .knowledge_base import MedicalKnowledgeBase, make_frame_id
from .models import DiagnosisReport, DiagnosisResult, Frame, PatientProfile


class DiagnosisEngine:
    """Explainable diagnosis scorer built on top of a semantic network."""

    def __init__(self, knowledge_base: MedicalKnowledgeBase | None = None) -> None:
        self.knowledge_base = knowledge_base or MedicalKnowledgeBase()

    def diagnose(self, patient: PatientProfile, top_n: int = 3) -> DiagnosisReport:
        symptoms, unknown_symptoms = self.knowledge_base.canonicalize_terms(patient.symptoms)
        risk_factors, unknown_risks = self.knowledge_base.canonicalize_terms(patient.risk_factors)
        unknown_terms = unknown_symptoms + unknown_risks

        patient_frame = Frame(
            frame_id=make_frame_id("patient", "current_patient"),
            frame_type="patient",
            name="Current Patient",
            slots={
                "symptoms": symptoms,
                "risk_factors": risk_factors,
                "age": patient.age,
                "duration_days": patient.duration_days,
                "vitals": patient.vitals,
            },
        )

        results: list[DiagnosisResult] = []

        for disease in self.knowledge_base.get_frames_by_type("disease"):
            symptom_weights = self.knowledge_base.disease_symptom_weights(disease.name)
            total_weight = sum(symptom_weights.values()) or 1.0

            matched_symptoms = [symptom for symptom in symptoms if symptom in symptom_weights]
            matched_weight = sum(symptom_weights[symptom] for symptom in matched_symptoms)
            coverage_score = matched_weight / total_weight
            patient_precision = len(matched_symptoms) / max(len(symptoms), 1)

            key_threshold = 0.16
            key_symptoms = [name for name, weight in symptom_weights.items() if weight >= key_threshold]
            missing_key_symptoms = [
                symptom for symptom in key_symptoms if symptom not in matched_symptoms
            ]
            key_match_score = (
                (len(key_symptoms) - len(missing_key_symptoms)) / len(key_symptoms)
                if key_symptoms
                else 0.0
            )

            disease_risk_factors = {
                risk.lower()
                for risk in self.knowledge_base.related_names(
                    disease.name, "associated_risk_factor"
                )
            }
            matched_risk_factors = sorted(disease_risk_factors.intersection(risk_factors))
            risk_score = (
                len(matched_risk_factors) / len(disease_risk_factors)
                if disease_risk_factors
                else 0.0
            )

            score = (coverage_score * 0.60) + (key_match_score * 0.20) + (
                patient_precision * 0.10
            ) + (risk_score * 0.10)

            if score < 0.10:
                continue

            supporting_tests = self.knowledge_base.related_names(disease.name, "suggests_test")
            evidence_paths = [
                f"Current Patient -> reports_symptom -> {symptom} <- has_symptom <- {disease.name}"
                for symptom in matched_symptoms
            ]
            if matched_risk_factors:
                evidence_paths.extend(
                    [
                        (
                            "Current Patient -> has_risk_factor -> "
                            f"{risk_factor} <- associated_risk_factor <- {disease.name}"
                        )
                        for risk_factor in matched_risk_factors
                    ]
                )

            results.append(
                DiagnosisResult(
                    disease_name=disease.name,
                    confidence=round(score, 3),
                    matched_symptoms=sorted(matched_symptoms),
                    matched_risk_factors=matched_risk_factors,
                    missing_key_symptoms=sorted(missing_key_symptoms),
                    supporting_tests=supporting_tests,
                    evidence_paths=evidence_paths,
                    explanation=self._build_explanation(
                        disease.name,
                        score,
                        matched_symptoms,
                        missing_key_symptoms,
                        matched_risk_factors,
                    ),
                )
            )

        results.sort(key=lambda item: item.confidence, reverse=True)
        detected_red_flags = sorted(set(symptoms).intersection(self.knowledge_base.red_flags))

        return DiagnosisReport(
            patient_frame=patient_frame,
            top_diagnoses=results[:top_n],
            detected_red_flags=detected_red_flags,
            unknown_terms=unknown_terms,
            graph_summary=self.knowledge_base.graph_summary(),
        )

    def _build_explanation(
        self,
        disease_name: str,
        confidence: float,
        matched_symptoms: list[str],
        missing_key_symptoms: list[str],
        matched_risk_factors: list[str],
    ) -> str:
        segments = [f"{disease_name} scored {confidence:.2f} from frame-slot overlap."]

        if matched_symptoms:
            segments.append("Matched symptoms: " + ", ".join(matched_symptoms) + ".")

        if matched_risk_factors:
            segments.append("Matched risk factors: " + ", ".join(matched_risk_factors) + ".")

        if missing_key_symptoms:
            segments.append(
                "Missing higher-signal symptoms: " + ", ".join(missing_key_symptoms) + "."
            )

        return " ".join(segments)
