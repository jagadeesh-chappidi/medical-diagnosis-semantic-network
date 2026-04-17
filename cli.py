from __future__ import annotations

import argparse
from pathlib import Path

from .diagnosis import DiagnosisEngine
from .knowledge_base import MedicalKnowledgeBase
from .models import PatientProfile
from .neo4j_export import Neo4jExporter


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Preliminary medical diagnosis using semantic networks and frames."
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch the desktop interface instead of printing CLI output.",
    )
    parser.add_argument(
        "--symptoms",
        nargs="*",
        default=[],
        help='Symptoms such as "fever" "cough" "loss of taste or smell".',
    )
    parser.add_argument(
        "--risk-factors",
        nargs="*",
        default=[],
        help='Risk factors such as "recent viral exposure" or "stress".',
    )
    parser.add_argument("--age", type=int, default=None, help="Patient age.")
    parser.add_argument(
        "--duration-days",
        type=int,
        default=None,
        help="Approximate duration of symptoms in days.",
    )
    parser.add_argument("--top", type=int, default=3, help="How many diagnoses to show.")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run a built-in demo patient when custom inputs are not provided.",
    )
    parser.add_argument(
        "--export-cypher",
        type=Path,
        default=None,
        help="Write the semantic network to a Neo4j Cypher file.",
    )
    parser.add_argument("--neo4j-uri", default=None, help="Neo4j URI such as bolt://localhost:7687")
    parser.add_argument("--neo4j-user", default=None, help="Neo4j username.")
    parser.add_argument("--neo4j-password", default=None, help="Neo4j password.")
    return parser


def demo_patient() -> PatientProfile:
    return PatientProfile(
        symptoms=["fever", "cough", "fatigue", "loss of smell"],
        risk_factors=["recent viral exposure"],
        age=42,
        duration_days=3,
    )


def format_report(report) -> str:
    lines: list[str] = []
    summary = report.graph_summary
    lines.append(
        "Knowledge graph summary: "
        f"{summary['nodes']} nodes, {summary['edges']} edges, {summary['diseases']} diseases."
    )
    lines.append(
        "Patient frame: "
        + ", ".join(
            [
                f"symptoms={report.patient_frame.get_slot('symptoms', [])}",
                f"risk_factors={report.patient_frame.get_slot('risk_factors', [])}",
                f"age={report.patient_frame.get_slot('age')}",
                f"duration_days={report.patient_frame.get_slot('duration_days')}",
            ]
        )
    )

    if report.detected_red_flags:
        lines.append("Urgent red flags detected: " + ", ".join(report.detected_red_flags))
    else:
        lines.append("Urgent red flags detected: none")

    if report.unknown_terms:
        lines.append("Unrecognized inputs: " + ", ".join(report.unknown_terms))

    if not report.top_diagnoses:
        lines.append("No strong diagnosis candidates were produced from the supplied evidence.")
        return "\n".join(lines)

    lines.append("Top diagnosis candidates:")
    for index, result in enumerate(report.top_diagnoses, start=1):
        lines.append(f"{index}. {result.disease_name} | confidence={result.confidence:.3f}")
        lines.append("   matched symptoms: " + ", ".join(result.matched_symptoms or ["none"]))
        lines.append(
            "   matched risk factors: " + ", ".join(result.matched_risk_factors or ["none"])
        )
        lines.append(
            "   missing key symptoms: " + ", ".join(result.missing_key_symptoms or ["none"])
        )
        lines.append("   suggested tests: " + ", ".join(result.supporting_tests or ["none"]))
        lines.append("   explanation: " + result.explanation)

    lines.append(
        "Clinical caution: this tool is for preliminary educational support and not medical advice."
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    knowledge_base = MedicalKnowledgeBase()
    engine = DiagnosisEngine(knowledge_base)
    exporter = Neo4jExporter(knowledge_base)

    if args.export_cypher:
        path = exporter.write_cypher(args.export_cypher)
        print(f"Wrote Neo4j Cypher export to {path}")

    if args.neo4j_uri and args.neo4j_user and args.neo4j_password:
        exporter.push(args.neo4j_uri, args.neo4j_user, args.neo4j_password)
        print(f"Pushed semantic network to Neo4j at {args.neo4j_uri}")

    if args.gui:
        from .gui import launch_gui

        launch_gui(knowledge_base=knowledge_base)
        return 0

    patient = demo_patient() if args.demo or not args.symptoms else PatientProfile(
        symptoms=args.symptoms,
        risk_factors=args.risk_factors,
        age=args.age,
        duration_days=args.duration_days,
    )
    report = engine.diagnose(patient, top_n=args.top)
    print(format_report(report))
    return 0
