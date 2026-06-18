from __future__ import annotations

import ipaddress
from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class VRP:
    prefix: str
    max_length: int
    origin_as: int
    source: str


def normalize_vrp(row: dict[str, object]) -> VRP:
    network = ipaddress.ip_network(str(row["prefix"]), strict=False)
    maximum = row.get("maxLength", row.get("max_length", network.prefixlen))
    asn = row.get("asn", row.get("origin_as"))
    if isinstance(asn, str) and asn.upper().startswith("AS"):
        asn = asn[2:]
    source = row.get("ta", row.get("source", ""))
    return VRP(str(network), int(maximum), int(asn), str(source))


def compare(baseline: set[VRP], candidate: set[VRP]) -> dict[str, object]:
    only_baseline = sorted(baseline - candidate)
    only_candidate = sorted(candidate - baseline)
    serialize = lambda value: {
        "prefix": value.prefix, "maxLength": value.max_length,
        "origin_as": value.origin_as, "source": value.source,
    }
    return {
        "baseline_count": len(baseline),
        "candidate_count": len(candidate),
        "equivalent": not only_baseline and not only_candidate,
        "only_baseline": [serialize(value) for value in only_baseline],
        "only_candidate": [serialize(value) for value in only_candidate],
    }
