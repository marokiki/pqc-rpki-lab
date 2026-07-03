#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from pqc_rpki_lab.mixed_tree import default_mixed_tree_fixture, validate_mixed_tree
from pqc_rpki_lab.result_io import markdown_table, write_json

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "mixed-tree"
TESTDATA = ROOT / "testdata" / "mixed-tree"


def main() -> None:
    fixture = default_mixed_tree_fixture()
    validation = validate_mixed_tree(fixture)
    nodes = [asdict(node) for node in fixture.nodes]
    products = list(fixture.products)
    document = {
        "warning": "EXPERIMENTAL / NOT FOR PRODUCTION",
        "classification": "public synthetic model; no private keys or operational RPKI objects",
        "nodes": nodes,
        "products": products,
        "validation": validation,
    }
    write_json(RESULTS / "mixed-tree.json", document)
    write_json(TESTDATA / "topology.json", document)
    (RESULTS / "mixed-tree.md").write_text(
        "# Mixed-Tree Fixture\n\n"
        "> EXPERIMENTAL / NOT FOR PRODUCTION\n\n"
        "This is a public synthetic model for CA-boundary algorithm transitions. It is not "
        "validator interoperability evidence and contains no private keys.\n\n"
        "## Certificates\n\n"
        + markdown_table(nodes, [
            ("name", "Name"), ("issuer", "Issuer"), ("spki_algorithm", "SPKI"),
            ("issuer_signature_algorithm", "Issuer Signature"),
        ])
        + "\n\n## Products\n\n"
        + markdown_table(products, [
            ("path", "Path"), ("object_type", "Type"), ("issuer", "Issuer"),
            ("signature_algorithm", "Signature"), ("publication_scope_key_id", "Scope Key"),
        ])
        + f"\n\nValidation: `{validation['valid']}`.\n"
    )


if __name__ == "__main__":
    main()
