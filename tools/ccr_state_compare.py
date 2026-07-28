#!/usr/bin/env python3
"""Compare state hashes extracted from actual RP-produced CCR files."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from pqc_rpki_lab.cms import decode_oid, parse_one

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULT = (
    ROOT / "results" / "ccr-comparison"
    / "rp-produced-state-hashes.json"
)
CCR_OID = "1.2.840.113549.1.9.16.1.54"
SHA256_OID = "2.16.840.1.101.3.4.2.1"
STATE_TAGS = {
    0xA1: "manifest_state",
    0xA2: "roa_payload_state",
    0xA3: "aspa_payload_state",
    0xA4: "trust_anchor_state",
    0xA5: "router_key_state",
}


def extract(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    root, end = parse_one(data)
    if end != len(data) or root.tag != 0x30:
        raise ValueError("CCR is not one DER SEQUENCE")
    content_info = root.children()
    if decode_oid(content_info[0]) != CCR_OID:
        raise ValueError("unexpected CCR content type")
    content = content_info[1].children()[0]
    fields = content.children()
    algorithm = fields[0].children()
    if len(algorithm) != 1 or decode_oid(algorithm[0]) != SHA256_OID:
        raise ValueError("CCR does not use SHA-256 with absent parameters")
    states = {}
    for field in fields[2:]:
        name = STATE_TAGS.get(field.tag)
        if name is None:
            continue
        state = field.children()[0].children()
        collection = state[0]
        digest = state[-1]
        if digest.tag != 0x04:
            raise ValueError(f"{name} does not end in a digest")
        calculated = hashlib.sha256(collection.encoded).digest()
        states[name] = {
            "hash_hex": digest.value.hex(),
            "hash_verified": calculated == digest.value,
            "item_count": len(collection.children()),
        }
    return {
        "file_sha256": hashlib.sha256(data).hexdigest(),
        "content_type": CCR_OID,
        "hash_algorithm": SHA256_OID,
        "produced_at": fields[1].value.decode("ascii"),
        "states": states,
    }


def parse_input(value: str) -> tuple[str, Path]:
    try:
        label, path = value.split("=", 1)
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            "inputs must use LABEL=PATH form"
        ) from error
    if not re.fullmatch(r"[A-Za-z0-9._-]+", label):
        raise argparse.ArgumentTypeError("input label contains unsafe characters")
    return label, Path(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input", action="append", type=parse_input, required=True
    )
    parser.add_argument("--result", type=Path, default=DEFAULT_RESULT)
    args = parser.parse_args()
    if len(args.input) < 2:
        raise SystemExit("at least two --input values are required")
    if len({label for label, _ in args.input}) != len(args.input):
        raise SystemExit("input labels must be unique")

    inputs = {
        label: extract(path.resolve()) for label, path in args.input
    }
    state_names = sorted(
        set.intersection(
            *(set(value["states"]) for value in inputs.values())
        )
    )
    comparisons = {}
    for state in state_names:
        hashes = {
            label: value["states"][state]["hash_hex"]
            for label, value in inputs.items()
        }
        comparisons[state] = {
            "equal": len(set(hashes.values())) == 1,
            "hashes": hashes,
        }
    document = {
        "warning": "EXPERIMENTAL / NOT FOR PRODUCTION",
        "classification": (
            "state hashes extracted from actual rpki-client CCR DER output; "
            "input CCR files remain below local/"
        ),
        "draft_profile": "draft-ietf-sidrops-rpki-ccr-11",
        "inputs": inputs,
        "comparisons": comparisons,
        "semantic_equivalence_field": "roa_payload_state",
        "provenance_field_kept_separate": "trust_anchor_state",
        "all_embedded_hashes_verified": all(
            state["hash_verified"]
            for value in inputs.values()
            for state in value["states"].values()
        ),
        "contains_raw_ccr": False,
        "contains_absolute_paths": False,
    }
    text = json.dumps(document, indent=2, sort_keys=True) + "\n"
    if re.search(r'/(?:home|Users)/', text):
        raise RuntimeError("sanitized summary contains an absolute user path")
    args.result.parent.mkdir(parents=True, exist_ok=True)
    args.result.write_text(text)
    print(text, end="")
    return 0 if document["all_embedded_hashes_verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
