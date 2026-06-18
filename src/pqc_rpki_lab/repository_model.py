from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AlgorithmSize:
    name: str
    public_key_bytes: int
    signature_bytes: int


@dataclass(frozen=True)
class Corpus:
    ca_certificates: int
    ee_certificates: int
    crls: int
    manifests: int
    roas: int
    ca_certificate: int
    ee_certificate: int
    crl: int
    manifest_payload: int
    roa_payload: int
    rrdp_xml_overhead_ratio: float = 0.12
    local_cache_overhead_ratio: float = 0.05
    rrdp_delta_changed_fraction: float = 0.10


def estimate_repository_bytes(corpus: Corpus, algorithm: AlgorithmSize) -> dict[str, int | str]:
    ca = corpus.ca_certificates * (corpus.ca_certificate + algorithm.public_key_bytes + algorithm.signature_bytes)
    ee = corpus.ee_certificates * (corpus.ee_certificate + algorithm.public_key_bytes + algorithm.signature_bytes)
    crl = corpus.crls * (corpus.crl + algorithm.signature_bytes)
    manifest = corpus.manifests * (corpus.manifest_payload + algorithm.signature_bytes)
    roa = corpus.roas * (corpus.roa_payload + algorithm.signature_bytes)
    total = ca + ee + crl + manifest + roa
    snapshot = round(total * (1 + corpus.rrdp_xml_overhead_ratio))
    return {
        "algorithm": algorithm.name,
        "ca_cert_total_bytes": ca,
        "crl_total_bytes": crl,
        "ee_cert_total_bytes": ee,
        "local_cache_bytes": round(total * (1 + corpus.local_cache_overhead_ratio)),
        "manifest_total_bytes": manifest,
        "model": "first-order component-size estimator",
        "repository_total_bytes": total,
        "roa_total_bytes": roa,
        "rrdp_delta_bytes": round(snapshot * corpus.rrdp_delta_changed_fraction),
        "rrdp_snapshot_bytes": snapshot,
        "status": "estimated",
    }
