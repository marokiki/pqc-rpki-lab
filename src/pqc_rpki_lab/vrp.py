from __future__ import annotations

import ipaddress
import hashlib
import json
from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class VRP:
    prefix: str
    max_length: int
    origin_as: int
    source: str


def semantic_key(value: VRP) -> tuple[int, int, bytes, int, int]:
    network = ipaddress.ip_network(value.prefix)
    return (network.version, value.origin_as, network.network_address.packed,
            network.prefixlen, value.max_length)


def semantic_row(value: VRP) -> dict[str, object]:
    return {
        "prefix": value.prefix,
        "maxLength": value.max_length,
        "origin_as": value.origin_as,
    }


def local_canonical_hash(values: set[VRP]) -> str:
    """Hash a stable local VRP representation; this is not CCR DER."""
    rows = [semantic_row(value) for value in sorted(values, key=semantic_key)]
    unique = list({json.dumps(row, sort_keys=True, separators=(",", ":")): row
                   for row in rows}.values())
    payload = json.dumps(unique, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def normalize_vrp(row: dict[str, object]) -> VRP:
    network = ipaddress.ip_network(str(row["prefix"]), strict=False)
    maximum = row.get("maxLength", row.get("max_length", network.prefixlen))
    asn = row.get("asn", row.get("origin_as"))
    if isinstance(asn, str) and asn.upper().startswith("AS"):
        asn = asn[2:]
    source = row.get("ta", row.get("source", ""))
    return VRP(str(network), int(maximum), int(asn), str(source))


def compare(baseline: set[VRP], candidate: set[VRP]) -> dict[str, object]:
    baseline_semantic = {semantic_key(value): value for value in baseline}
    candidate_semantic = {semantic_key(value): value for value in candidate}
    only_baseline_keys = sorted(baseline_semantic.keys() - candidate_semantic.keys())
    only_candidate_keys = sorted(candidate_semantic.keys() - baseline_semantic.keys())
    only_baseline = [baseline_semantic[key] for key in only_baseline_keys]
    only_candidate = [candidate_semantic[key] for key in only_candidate_keys]
    common = baseline_semantic.keys() & candidate_semantic.keys()
    baseline_sources = {key: sorted({value.source for value in baseline if semantic_key(value) == key})
                        for key in common}
    candidate_sources = {key: sorted({value.source for value in candidate if semantic_key(value) == key})
                         for key in common}
    provenance_differences = [
        semantic_row(baseline_semantic[key]) | {
            "baseline_sources": baseline_sources[key],
            "candidate_sources": candidate_sources[key],
        }
        for key in sorted(common)
        if baseline_sources[key] != candidate_sources[key]
    ]
    return {
        "baseline_count": len(baseline_semantic),
        "candidate_count": len(candidate_semantic),
        "equivalent": not only_baseline and not only_candidate,
        "local_hash_algorithm": "sha256-canonical-json-v1-not-ccr",
        "baseline_local_hash": local_canonical_hash(baseline),
        "candidate_local_hash": local_canonical_hash(candidate),
        "only_baseline": [semantic_row(value) for value in only_baseline],
        "only_candidate": [semantic_row(value) for value in only_candidate],
        "provenance_differences": provenance_differences,
    }
