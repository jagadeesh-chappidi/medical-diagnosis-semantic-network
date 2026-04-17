from __future__ import annotations

from typing import Any
import re

import networkx as nx

from .models import Frame

SYMPTOM_CATALOG: dict[str, dict[str, Any]] = {
    "fever": {
        "body_system": "systemic",
        "description": "Elevated body temperature associated with infection or inflammation.",
    },
    "cough": {
        "body_system": "respiratory",
        "description": "Protective reflex caused by airway irritation or infection.",
    },
    "sore throat": {
        "body_system": "respiratory",
        "description": "Pain or irritation of the throat.",
    },
    "fatigue": {
        "body_system": "systemic",
        "description": "Unusual tiredness or low energy.",
    },
    "headache": {
        "body_system": "neurological",
        "description": "General head pain or pressure.",
    },
    "body ache": {
        "body_system": "musculoskeletal",
        "description": "Generalized muscle or body pain.",
    },
    "nasal congestion": {
        "body_system": "respiratory",
        "description": "Blocked or stuffy nose.",
    },
    "sneezing": {
        "body_system": "respiratory",
        "description": "Sudden expulsion of air through the nose and mouth.",
    },
    "loss of taste or smell": {
        "body_system": "neurological",
        "description": "Reduced or absent sense of smell or taste.",
    },
    "nausea": {
        "body_system": "gastrointestinal",
        "description": "Sensation of wanting to vomit.",
    },
    "vomiting": {
        "body_system": "gastrointestinal",
        "description": "Forceful expulsion of stomach contents.",
    },
    "diarrhea": {
        "body_system": "gastrointestinal",
        "description": "Loose or watery stools.",
    },
    "abdominal pain": {
        "body_system": "gastrointestinal",
        "description": "Pain in the abdomen.",
    },
    "photophobia": {
        "body_system": "neurological",
        "description": "Sensitivity to light.",
    },
    "unilateral headache": {
        "body_system": "neurological",
        "description": "Head pain predominantly on one side.",
    },
    "rash": {
        "body_system": "dermatological",
        "description": "Visible skin eruption or discoloration.",
    },
    "joint pain": {
        "body_system": "musculoskeletal",
        "description": "Pain in one or more joints.",
    },
    "retro-orbital pain": {
        "body_system": "neurological",
        "description": "Pain behind the eyes.",
    },
    "chills": {
        "body_system": "systemic",
        "description": "Shivering sensation often associated with fever.",
    },
    "shortness of breath": {
        "body_system": "respiratory",
        "description": "Difficulty breathing or air hunger.",
    },
    "dehydration": {
        "body_system": "systemic",
        "description": "Fluid depletion causing dry mouth, weakness, or dizziness.",
    },
    "stiff neck": {
        "body_system": "neurological",
        "description": "Painful neck rigidity that may indicate urgent illness.",
    },
    "confusion": {
        "body_system": "neurological",
        "description": "Altered mental state or disorientation.",
    },
    "chest pain": {
        "body_system": "cardiorespiratory",
        "description": "Pain or tightness in the chest.",
    },
    "severe abdominal pain": {
        "body_system": "gastrointestinal",
        "description": "Severe abdominal pain that warrants urgent evaluation.",
    },
}

RISK_FACTOR_CATALOG: dict[str, dict[str, Any]] = {
    "recent viral exposure": {"description": "Recent close contact with an infected person."},
    "weak immunity": {"description": "Immunocompromised or reduced immune defenses."},
    "older age": {"description": "Age-associated vulnerability to severe infection."},
    "travel to mosquito-prone area": {
        "description": "Recent travel to an area where mosquito-borne disease is common."
    },
    "contaminated food intake": {
        "description": "Recent ingestion of possibly unsafe or spoiled food."
    },
    "stress": {"description": "Stress is a common migraine trigger."},
    "sleep deprivation": {"description": "Lack of sleep can worsen headaches and immunity."},
    "chronic respiratory condition": {
        "description": "Underlying respiratory disease increases pulmonary infection risk."
    },
}

TEST_CATALOG: dict[str, dict[str, Any]] = {
    "COVID-19 RT-PCR": {"test_type": "laboratory", "description": "Confirms SARS-CoV-2 infection."},
    "Rapid Influenza Antigen": {
        "test_type": "laboratory",
        "description": "Rapid screening test for influenza virus.",
    },
    "Complete Blood Count (CBC)": {
        "test_type": "laboratory",
        "description": "Evaluates infection-related blood count patterns.",
    },
    "Chest X-ray": {"test_type": "imaging", "description": "Assesses lung infiltrates."},
    "Pulse Oximetry": {
        "test_type": "bedside",
        "description": "Checks blood oxygen saturation.",
    },
    "Dengue NS1 Antigen": {
        "test_type": "laboratory",
        "description": "Early laboratory support for dengue infection.",
    },
    "Stool Culture": {
        "test_type": "laboratory",
        "description": "Investigates bacterial gastrointestinal infection.",
    },
    "Neurological Examination": {
        "test_type": "clinical",
        "description": "Evaluates neurological status and focal signs.",
    },
}

DISEASE_LIBRARY: list[dict[str, Any]] = [
    {
        "name": "Influenza",
        "category": "viral infection",
        "description": "Acute respiratory viral illness with fever, cough, and myalgia.",
        "systems": ["respiratory", "systemic"],
        "symptoms": {
            "fever": 0.24,
            "cough": 0.16,
            "fatigue": 0.14,
            "body ache": 0.18,
            "headache": 0.12,
            "sore throat": 0.10,
            "chills": 0.06,
        },
        "risk_factors": ["recent viral exposure", "weak immunity", "older age"],
        "recommended_tests": ["Rapid Influenza Antigen", "Complete Blood Count (CBC)"],
        "urgent_red_flags": ["shortness of breath", "chest pain", "confusion"],
        "differential_diagnoses": ["Common Cold", "COVID-19", "Pneumonia"],
    },
    {
        "name": "Common Cold",
        "category": "upper respiratory infection",
        "description": "Mild viral upper respiratory tract infection dominated by nasal symptoms.",
        "systems": ["respiratory"],
        "symptoms": {
            "sneezing": 0.22,
            "nasal congestion": 0.20,
            "sore throat": 0.16,
            "cough": 0.12,
            "headache": 0.10,
            "fatigue": 0.10,
            "fever": 0.10,
        },
        "risk_factors": ["recent viral exposure", "weak immunity"],
        "recommended_tests": ["Complete Blood Count (CBC)"],
        "urgent_red_flags": ["shortness of breath", "chest pain"],
        "differential_diagnoses": ["Influenza", "COVID-19"],
    },
    {
        "name": "COVID-19",
        "category": "viral infection",
        "description": "Respiratory viral illness with variable systemic involvement.",
        "systems": ["respiratory", "systemic"],
        "symptoms": {
            "fever": 0.16,
            "cough": 0.16,
            "fatigue": 0.14,
            "loss of taste or smell": 0.22,
            "shortness of breath": 0.14,
            "headache": 0.08,
            "sore throat": 0.10,
        },
        "risk_factors": ["recent viral exposure", "older age", "weak immunity"],
        "recommended_tests": ["COVID-19 RT-PCR", "Pulse Oximetry", "Complete Blood Count (CBC)"],
        "urgent_red_flags": ["shortness of breath", "chest pain", "confusion"],
        "differential_diagnoses": ["Influenza", "Common Cold", "Pneumonia"],
    },
    {
        "name": "Migraine",
        "category": "neurological disorder",
        "description": "Recurrent neurovascular headache syndrome with sensory sensitivity.",
        "systems": ["neurological"],
        "symptoms": {
            "unilateral headache": 0.30,
            "headache": 0.12,
            "photophobia": 0.26,
            "nausea": 0.18,
            "vomiting": 0.14,
        },
        "risk_factors": ["stress", "sleep deprivation"],
        "recommended_tests": ["Neurological Examination"],
        "urgent_red_flags": ["stiff neck", "confusion"],
        "differential_diagnoses": ["Influenza"],
    },
    {
        "name": "Food Poisoning",
        "category": "gastrointestinal illness",
        "description": "Acute gastrointestinal upset related to unsafe food or infection.",
        "systems": ["gastrointestinal", "systemic"],
        "symptoms": {
            "nausea": 0.22,
            "vomiting": 0.20,
            "diarrhea": 0.24,
            "abdominal pain": 0.18,
            "fever": 0.08,
            "dehydration": 0.08,
        },
        "risk_factors": ["contaminated food intake"],
        "recommended_tests": ["Stool Culture", "Complete Blood Count (CBC)"],
        "urgent_red_flags": ["dehydration", "confusion", "severe abdominal pain"],
        "differential_diagnoses": ["Dengue Fever"],
    },
    {
        "name": "Dengue Fever",
        "category": "mosquito-borne viral infection",
        "description": "Systemic viral illness often marked by fever, headache, and severe body pains.",
        "systems": ["systemic", "hematological"],
        "symptoms": {
            "fever": 0.20,
            "headache": 0.14,
            "retro-orbital pain": 0.18,
            "joint pain": 0.18,
            "rash": 0.12,
            "nausea": 0.10,
            "fatigue": 0.08,
        },
        "risk_factors": ["travel to mosquito-prone area"],
        "recommended_tests": ["Dengue NS1 Antigen", "Complete Blood Count (CBC)"],
        "urgent_red_flags": ["confusion", "severe abdominal pain", "dehydration"],
        "differential_diagnoses": ["Influenza", "Food Poisoning"],
    },
    {
        "name": "Pneumonia",
        "category": "lower respiratory infection",
        "description": "Infection of the lungs that may impair oxygenation.",
        "systems": ["respiratory", "systemic"],
        "symptoms": {
            "fever": 0.16,
            "cough": 0.18,
            "shortness of breath": 0.22,
            "chest pain": 0.16,
            "fatigue": 0.12,
            "chills": 0.08,
            "body ache": 0.08,
        },
        "risk_factors": ["older age", "weak immunity", "chronic respiratory condition"],
        "recommended_tests": ["Chest X-ray", "Pulse Oximetry", "Complete Blood Count (CBC)"],
        "urgent_red_flags": ["shortness of breath", "chest pain", "confusion"],
        "differential_diagnoses": ["Influenza", "COVID-19"],
    },
]

TERM_ALIASES: dict[str, str] = {
    "loss of smell": "loss of taste or smell",
    "loss of taste": "loss of taste or smell",
    "anosmia": "loss of taste or smell",
    "runny nose": "nasal congestion",
    "body pain": "body ache",
    "muscle pain": "body ache",
    "difficulty breathing": "shortness of breath",
    "breathlessness": "shortness of breath",
    "stomach pain": "abdominal pain",
    "light sensitivity": "photophobia",
    "one sided headache": "unilateral headache",
}

GLOBAL_RED_FLAGS = {
    "shortness of breath",
    "chest pain",
    "confusion",
    "stiff neck",
    "dehydration",
    "severe abdominal pain",
}


def make_frame_id(kind: str, name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return f"{kind}:{slug}"


class MedicalKnowledgeBase:
    """Knowledge base built from explicit frames and a semantic network."""

    def __init__(self) -> None:
        self.graph = nx.MultiDiGraph()
        self.frames_by_id: dict[str, Frame] = {}
        self.frame_ids_by_name: dict[str, str] = {}
        self._bootstrap()

    def _bootstrap(self) -> None:
        self._add_catalog_frames()
        self._add_disease_frames()

    def _add_catalog_frames(self) -> None:
        body_systems = {details["body_system"] for details in SYMPTOM_CATALOG.values()}
        body_systems.update(system for disease in DISEASE_LIBRARY for system in disease["systems"])

        for system in sorted(body_systems):
            system_frame = Frame(
                frame_id=make_frame_id("system", system),
                frame_type="body_system",
                name=system,
                slots={"description": f"{system.title()} clinical domain."},
            )
            self._add_frame(system_frame)

        for symptom_name, details in SYMPTOM_CATALOG.items():
            frame = Frame(
                frame_id=make_frame_id("symptom", symptom_name),
                frame_type="symptom",
                name=symptom_name,
                slots=details,
            )
            self._add_frame(frame)
            self._add_edge(
                frame.frame_id,
                make_frame_id("system", details["body_system"]),
                relation="belongs_to_system",
            )

        for risk_name, details in RISK_FACTOR_CATALOG.items():
            frame = Frame(
                frame_id=make_frame_id("risk", risk_name),
                frame_type="risk_factor",
                name=risk_name,
                slots=details,
            )
            self._add_frame(frame)

        for test_name, details in TEST_CATALOG.items():
            frame = Frame(
                frame_id=make_frame_id("test", test_name),
                frame_type="test",
                name=test_name,
                slots=details,
            )
            self._add_frame(frame)

    def _add_disease_frames(self) -> None:
        for disease in DISEASE_LIBRARY:
            frame = Frame(
                frame_id=make_frame_id("disease", disease["name"]),
                frame_type="disease",
                name=disease["name"],
                slots={
                    "category": disease["category"],
                    "description": disease["description"],
                    "systems": disease["systems"],
                    "symptoms": disease["symptoms"],
                    "risk_factors": disease["risk_factors"],
                    "recommended_tests": disease["recommended_tests"],
                    "urgent_red_flags": disease["urgent_red_flags"],
                    "differential_diagnoses": disease["differential_diagnoses"],
                },
            )
            self._add_frame(frame)

            for system in disease["systems"]:
                self._add_edge(
                    frame.frame_id,
                    make_frame_id("system", system),
                    relation="affects_system",
                )

            for symptom_name, weight in disease["symptoms"].items():
                self._add_edge(
                    frame.frame_id,
                    make_frame_id("symptom", symptom_name),
                    relation="has_symptom",
                    weight=weight,
                )

            for risk_factor in disease["risk_factors"]:
                self._add_edge(
                    frame.frame_id,
                    make_frame_id("risk", risk_factor),
                    relation="associated_risk_factor",
                )

            for test_name in disease["recommended_tests"]:
                self._add_edge(
                    frame.frame_id,
                    make_frame_id("test", test_name),
                    relation="suggests_test",
                )

            for red_flag in disease["urgent_red_flags"]:
                self._add_edge(
                    frame.frame_id,
                    make_frame_id("symptom", red_flag),
                    relation="urgent_red_flag",
                )

        for disease in DISEASE_LIBRARY:
            disease_id = make_frame_id("disease", disease["name"])
            for differential in disease["differential_diagnoses"]:
                self._add_edge(
                    disease_id,
                    make_frame_id("disease", differential),
                    relation="differential_diagnosis",
                )

    def _add_frame(self, frame: Frame) -> None:
        self.frames_by_id[frame.frame_id] = frame
        self.frame_ids_by_name[frame.name.lower()] = frame.frame_id
        self.graph.add_node(
            frame.frame_id,
            name=frame.name,
            frame_type=frame.frame_type,
            slots=frame.slots,
        )

    def _add_edge(self, source: str, target: str, relation: str, **attributes: Any) -> None:
        self.graph.add_edge(source, target, key=relation, relation=relation, **attributes)

    def get_frame(self, name_or_id: str) -> Frame:
        frame_id = self.frame_ids_by_name.get(name_or_id.lower(), name_or_id)
        return self.frames_by_id[frame_id]

    def get_frames_by_type(self, frame_type: str) -> list[Frame]:
        return [frame for frame in self.frames_by_id.values() if frame.frame_type == frame_type]

    def canonicalize_term(self, term: str) -> str | None:
        normalized = term.strip().lower()
        if normalized in self.frame_ids_by_name:
            return self.get_frame(normalized).name.lower()

        alias_target = TERM_ALIASES.get(normalized)
        if alias_target:
            return alias_target

        return None

    def canonicalize_terms(self, terms: list[str]) -> tuple[list[str], list[str]]:
        recognized: list[str] = []
        unknown: list[str] = []

        for term in terms:
            canonical = self.canonicalize_term(term)
            if canonical is None:
                unknown.append(term)
                continue
            if canonical not in recognized:
                recognized.append(canonical)

        return recognized, unknown

    def disease_symptom_weights(self, disease_name: str) -> dict[str, float]:
        disease_id = self.get_frame(disease_name).frame_id
        mapping: dict[str, float] = {}

        for _, symptom_id, _, edge_data in self.graph.out_edges(disease_id, keys=True, data=True):
            if edge_data["relation"] != "has_symptom":
                continue
            symptom_name = self.graph.nodes[symptom_id]["name"].lower()
            mapping[symptom_name] = float(edge_data.get("weight", 0.0))

        return mapping

    def related_names(self, name: str, relation: str) -> list[str]:
        frame_id = self.get_frame(name).frame_id
        neighbors: list[str] = []

        for _, target_id, _, edge_data in self.graph.out_edges(frame_id, keys=True, data=True):
            if edge_data["relation"] == relation:
                neighbors.append(self.graph.nodes[target_id]["name"])

        return sorted(neighbors)

    def graph_summary(self) -> dict[str, int]:
        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "diseases": len(self.get_frames_by_type("disease")),
            "symptoms": len(self.get_frames_by_type("symptom")),
            "risk_factors": len(self.get_frames_by_type("risk_factor")),
            "tests": len(self.get_frames_by_type("test")),
        }

    def node_rows(self) -> list[dict[str, Any]]:
        return [
            {
                "id": frame.frame_id,
                "name": frame.name,
                "frame_type": frame.frame_type,
                "slots": frame.slots,
            }
            for frame in self.frames_by_id.values()
        ]

    def edge_rows(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for source, target, _, data in self.graph.edges(keys=True, data=True):
            rows.append(
                {
                    "source": source,
                    "target": target,
                    "relation": data["relation"],
                    "weight": data.get("weight"),
                }
            )
        return rows

    @property
    def red_flags(self) -> set[str]:
        return set(GLOBAL_RED_FLAGS)
