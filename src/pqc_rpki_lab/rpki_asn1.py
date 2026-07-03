from __future__ import annotations

import hashlib
import ipaddress

from pqc_rpki_lab import der
from pqc_rpki_lab.cms import decode_integer, decode_oid, parse_one

OID_CT_ROA = "1.2.840.113549.1.9.16.1.24"
OID_CT_MFT = "1.2.840.113549.1.9.16.1.26"
OID_SHA256 = "2.16.840.1.101.3.4.2.1"


def _prefix_bit_string(prefix: str) -> bytes:
    network = ipaddress.ip_network(prefix, strict=False)
    used_octets = (network.prefixlen + 7) // 8
    unused_bits = (8 - (network.prefixlen % 8)) % 8
    value = network.network_address.packed[:used_octets]
    if unused_bits and value:
        value = value[:-1] + bytes([value[-1] & (0xFF << unused_bits)])
    return der.bit_string(value, unused_bits)


def roa_ip_address(prefix: str, max_length: int | None = None) -> bytes:
    network = ipaddress.ip_network(prefix, strict=False)
    fields = [_prefix_bit_string(str(network))]
    if max_length is not None and max_length != network.prefixlen:
        if max_length < network.prefixlen or max_length > network.max_prefixlen:
            raise ValueError("maxLength must be between prefix length and address length")
        fields.append(der.integer(max_length))
    return der.sequence(*fields)


def roa_ip_family(prefixes: list[tuple[str, int | None]]) -> bytes:
    if not prefixes:
        raise ValueError("ROA family requires at least one prefix")
    first = ipaddress.ip_network(prefixes[0][0], strict=False)
    afi = 1 if first.version == 4 else 2
    for prefix, _ in prefixes:
        if ipaddress.ip_network(prefix, strict=False).version != first.version:
            raise ValueError("ROAIPAddressFamily cannot mix IPv4 and IPv6")
    addresses = der.sequence(*(roa_ip_address(prefix, maximum) for prefix, maximum in prefixes))
    return der.sequence(der.octet_string(afi.to_bytes(2, "big")), addresses)


def roa_econtent(origin_as: int, prefixes: list[tuple[str, int | None]]) -> bytes:
    if origin_as <= 0:
        raise ValueError("origin AS must be positive")
    by_version: dict[int, list[tuple[str, int | None]]] = {}
    for prefix, maximum in prefixes:
        network = ipaddress.ip_network(prefix, strict=False)
        by_version.setdefault(network.version, []).append((str(network), maximum))
    families = [roa_ip_family(values) for _, values in sorted(by_version.items())]
    return der.sequence(der.integer(origin_as), der.sequence(*families))


def manifest_econtent(
    files: list[tuple[str, bytes]],
    *,
    manifest_number: int = 1,
    this_update: str = "20260101000000Z",
    next_update: str = "20260102000000Z",
) -> bytes:
    if manifest_number < 0:
        raise ValueError("manifestNumber must be non-negative")
    entries = []
    for name, content in sorted(files, key=lambda item: item[0]):
        if "/" in name or not name:
            raise ValueError("Manifest file names must be local IA5String names")
        digest = hashlib.sha256(content).digest()
        entries.append(der.sequence(der.ia5_string(name), der.bit_string(digest, 0)))
    return der.sequence(
        der.integer(manifest_number),
        der.generalized_time(this_update),
        der.generalized_time(next_update),
        der.object_identifier(OID_SHA256),
        der.sequence(*entries),
    )


def parse_manifest_econtent(value: bytes) -> dict[str, object]:
    root, end = parse_one(value)
    if end != len(value) or root.tag != 0x30:
        raise ValueError("Manifest eContent must be one DER SEQUENCE")
    fields = root.children()
    if fields and fields[0].tag == 0xA0:
        version = decode_integer(fields.pop(0).children()[0])
    else:
        version = 0
    if len(fields) != 5:
        raise ValueError("unexpected Manifest field count")
    entries = []
    for item in fields[4].children():
        parts = item.children()
        if len(parts) != 2 or parts[0].tag != 0x16 or parts[1].tag != 0x03 or not parts[1].value:
            raise ValueError("invalid FileAndHash")
        entries.append({
            "file": parts[0].value.decode("ascii"),
            "hash": parts[1].value[1:],
            "unused_bits": parts[1].value[0],
        })
    return {
        "version": version,
        "manifest_number": decode_integer(fields[0]),
        "this_update": fields[1].value.decode("ascii"),
        "next_update": fields[2].value.decode("ascii"),
        "file_hash_algorithm": decode_oid(fields[3]),
        "entries": entries,
    }
