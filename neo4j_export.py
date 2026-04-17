from __future__ import annotations

import json
import re
from pathlib import Path

from .knowledge_base import MedicalKnowledgeBase

try:
    from neo4j import GraphDatabase
except ImportError:  # pragma: no cover
    GraphDatabase = None


def cypher_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def relation_label(relation: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", relation.upper()).strip("_")


class Neo4jExporter:
    def __init__(self, knowledge_base: MedicalKnowledgeBase) -> None:
        self.knowledge_base = knowledge_base

    def generate_cypher(self) -> str:
        lines: list[str] = []

        for node in self.knowledge_base.node_rows():
            labels = f":Frame:{node['frame_type'].title().replace('_', '')}"
            lines.append(
                "MERGE (n"
                f"{labels} {{id: '{cypher_escape(node['id'])}'}}) "
                f"SET n.name = '{cypher_escape(node['name'])}', "
                f"n.frame_type = '{cypher_escape(node['frame_type'])}', "
                f"n.slots_json = '{cypher_escape(json.dumps(node['slots'], sort_keys=True))}';"
            )

        for edge in self.knowledge_base.edge_rows():
            weight_literal = (
                f", r.weight = {float(edge['weight'])}" if edge["weight"] is not None else ""
            )
            lines.append(
                f"MATCH (a {{id: '{cypher_escape(edge['source'])}'}}), "
                f"(b {{id: '{cypher_escape(edge['target'])}'}}) "
                f"MERGE (a)-[r:{relation_label(edge['relation'])}]->(b)"
                f" SET r.relation = '{cypher_escape(edge['relation'])}'{weight_literal};"
            )

        return "\n".join(lines) + "\n"

    def write_cypher(self, output_path: str | Path) -> Path:
        path = Path(output_path)
        path.write_text(self.generate_cypher(), encoding="utf-8")
        return path

    def push(self, uri: str, username: str, password: str) -> None:
        if GraphDatabase is None:
            raise RuntimeError(
                "The neo4j package is not installed. Install dependencies before pushing to Neo4j."
            )

        driver = GraphDatabase.driver(uri, auth=(username, password))
        statements = self.generate_cypher().strip().splitlines()

        with driver.session() as session:
            for statement in statements:
                session.run(statement)

        driver.close()
