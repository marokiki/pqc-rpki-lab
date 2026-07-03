from __future__ import annotations

import hashlib
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from pqc_rpki_lab import der

# RFC 5652, RFC 6488 as updated by RFC 9589, and RFC 9882.
OID_SIGNED_DATA = "1.2.840.113549.1.7.2"
OID_SHA512 = "2.16.840.1.101.3.4.2.3"
OID_ML_DSA_65 = "2.16.840.1.101.3.4.3.18"
OID_CONTENT_TYPE = "1.2.840.113549.1.9.3"
OID_MESSAGE_DIGEST = "1.2.840.113549.1.9.4"
OID_SIGNING_TIME = "1.2.840.113549.1.9.5"


@dataclass(frozen=True)
class Node:
    tag: int
    value: bytes
    encoded: bytes

    def children(self) -> list["Node"]:
        return parse_all(self.value)


def _read_length(data: bytes, offset: int) -> tuple[int, int]:
    if offset >= len(data):
        raise ValueError("truncated DER length")
    first = data[offset]
    if first < 0x80:
        return first, offset + 1
    count = first & 0x7F
    if count == 0 or count > 4 or offset + 1 + count > len(data):
        raise ValueError("invalid DER length")
    raw = data[offset + 1:offset + 1 + count]
    if raw[0] == 0 or (count == 1 and raw[0] < 0x80):
        raise ValueError("non-minimal DER length")
    return int.from_bytes(raw, "big"), offset + 1 + count


def parse_one(data: bytes, offset: int = 0) -> tuple[Node, int]:
    if offset >= len(data):
        raise ValueError("truncated DER tag")
    tag = data[offset]
    if tag & 0x1F == 0x1F:
        raise ValueError("high-tag-number DER is not supported")
    size, start = _read_length(data, offset + 1)
    end = start + size
    if end > len(data):
        raise ValueError("truncated DER value")
    return Node(tag, data[start:end], data[offset:end]), end


def parse_all(data: bytes) -> list[Node]:
    nodes: list[Node] = []
    offset = 0
    while offset < len(data):
        node, offset = parse_one(data, offset)
        nodes.append(node)
    return nodes


def decode_integer(node: Node) -> int:
    if node.tag != 0x02 or not node.value or node.value[0] & 0x80:
        raise ValueError("expected non-negative DER INTEGER")
    return int.from_bytes(node.value, "big")


def decode_oid(node: Node) -> str:
    if node.tag != 0x06 or not node.value:
        raise ValueError("expected OBJECT IDENTIFIER")
    first = node.value[0]
    arcs = [min(first // 40, 2), first - 40 * min(first // 40, 2)]
    value = 0
    pending = False
    for octet in node.value[1:]:
        value = (value << 7) | (octet & 0x7F)
        pending = bool(octet & 0x80)
        if not pending:
            arcs.append(value)
            value = 0
    if pending:
        raise ValueError("truncated OBJECT IDENTIFIER")
    return ".".join(str(arc) for arc in arcs)


def _attribute(oid: str, value: bytes) -> bytes:
    return der.sequence(der.object_identifier(oid), der.set_of(value))


def signed_attributes(econtent_type: str, econtent: bytes, signing_time: str) -> bytes:
    attributes = (
        _attribute(OID_CONTENT_TYPE, der.object_identifier(econtent_type)),
        _attribute(OID_MESSAGE_DIGEST, der.octet_string(hashlib.sha512(econtent).digest())),
        _attribute(OID_SIGNING_TIME, der.utc_time(signing_time)),
    )
    return der.set_of(*attributes)


def sign_raw_mldsa(openssl: str, key: Path, message: bytes) -> bytes:
    with tempfile.TemporaryDirectory(prefix="pqc-rpki-cms-sign-") as name:
        directory = Path(name)
        source = directory / "signed-attrs.der"
        signature = directory / "signature.bin"
        source.write_bytes(message)
        process = subprocess.run(
            [openssl, "pkeyutl", "-sign", "-rawin", "-inkey", str(key),
             "-in", str(source), "-out", str(signature)],
            capture_output=True, text=True,
        )
        if process.returncode:
            raise RuntimeError((process.stderr or process.stdout).strip())
        return signature.read_bytes()


def assemble_mldsa65_signed_object(
    *, econtent_type: str, econtent: bytes, ee_certificate_der: bytes,
    subject_key_identifier: bytes, signature: bytes, signing_time: str,
) -> bytes:
    attrs = signed_attributes(econtent_type, econtent, signing_time)
    signer_info = der.sequence(
        der.integer(3),
        der.tlv(0x80, subject_key_identifier),
        der.algorithm_identifier(OID_SHA512),
        der.tlv(0xA0, parse_one(attrs)[0].value),
        der.algorithm_identifier(OID_ML_DSA_65),
        der.octet_string(signature),
    )
    signed_data = der.sequence(
        der.integer(3),
        der.set_of(der.algorithm_identifier(OID_SHA512)),
        der.sequence(
            der.object_identifier(econtent_type),
            der.tlv(0xA0, der.octet_string(econtent)),
        ),
        der.tlv(0xA0, ee_certificate_der),
        der.set_of(signer_info),
    )
    return der.sequence(
        der.object_identifier(OID_SIGNED_DATA),
        der.tlv(0xA0, signed_data),
    )


def _algorithm(node: Node) -> tuple[str, bool]:
    children = node.children()
    if node.tag != 0x30 or not children:
        raise ValueError("invalid AlgorithmIdentifier")
    return decode_oid(children[0]), len(children) == 1


def inspect_signed_object(data: bytes) -> dict[str, object]:
    root, end = parse_one(data)
    if end != len(data) or root.tag != 0x30:
        raise ValueError("CMS ContentInfo must be one DER SEQUENCE")
    content_info = root.children()
    signed_data = content_info[1].children()[0]
    fields = signed_data.children()
    eci = fields[2].children()
    signer_info = fields[-1].children()[0]
    signer = signer_info.children()
    attrs = parse_all(signer[3].value)
    attribute_values: dict[str, list[Node]] = {}
    attribute_oids: list[str] = []
    for attribute in attrs:
        parts = attribute.children()
        oid = decode_oid(parts[0])
        attribute_oids.append(oid)
        attribute_values[oid] = parts[1].children()
    return {
        "content_info_oid": decode_oid(content_info[0]),
        "signed_data_version": decode_integer(fields[0]),
        "digest_algorithms": [_algorithm(node) for node in fields[1].children()],
        "econtent_type": decode_oid(eci[0]),
        "econtent": eci[1].children()[0].value,
        "certificate_count": len(fields[3].children()),
        "has_crls": any(node.tag == 0xA1 for node in fields[3:-1]),
        "signer_info_count": len(fields[-1].children()),
        "signer_version": decode_integer(signer[0]),
        "sid": signer[1].value,
        "digest_algorithm": _algorithm(signer[2]),
        "signed_attrs_der": der.tlv(0x31, signer[3].value),
        "attributes": attribute_values,
        "attribute_oids": attribute_oids,
        "signature_algorithm": _algorithm(signer[4]),
        "signature": signer[5].value,
        "has_unsigned_attrs": len(signer) != 6,
    }


def profile_check(data: bytes, *, expected_econtent_type: str, expected_ski: bytes) -> dict[str, object]:
    try:
        item = inspect_signed_object(data)
    except (IndexError, ValueError) as error:
        return {"valid": False, "checks": {"der_structure": False}, "error": str(error)}
    attrs = item["attributes"]
    assert isinstance(attrs, dict)
    allowed = {OID_CONTENT_TYPE, OID_MESSAGE_DIGEST, OID_SIGNING_TIME}
    content_values = attrs.get(OID_CONTENT_TYPE, [])
    digest_values = attrs.get(OID_MESSAGE_DIGEST, [])
    time_values = attrs.get(OID_SIGNING_TIME, [])
    checks = {
        "der_structure": True,
        "content_info_signed_data": item["content_info_oid"] == OID_SIGNED_DATA,
        "signed_data_version_3": item["signed_data_version"] == 3,
        "one_sha512_digest_algorithm_without_parameters": item["digest_algorithms"] == [(OID_SHA512, True)],
        "expected_econtent_type": item["econtent_type"] == expected_econtent_type,
        "one_ee_certificate": item["certificate_count"] == 1,
        "crls_omitted": not item["has_crls"],
        "one_signer_info": item["signer_info_count"] == 1,
        "signer_info_version_3": item["signer_version"] == 3,
        "sid_matches_ee_ski": item["sid"] == expected_ski,
        "sha512_digest_algorithm_without_parameters": item["digest_algorithm"] == (OID_SHA512, True),
        "exactly_three_allowed_signed_attributes": len(item["attribute_oids"]) == 3 and set(item["attribute_oids"]) == allowed and all(len(values) == 1 for values in attrs.values()),
        "content_type_attribute_matches": len(content_values) == 1 and decode_oid(content_values[0]) == expected_econtent_type,
        "message_digest_matches": len(digest_values) == 1 and digest_values[0].tag == 0x04 and digest_values[0].value == hashlib.sha512(item["econtent"]).digest(),
        "signing_time_present": len(time_values) == 1 and time_values[0].tag in (0x17, 0x18),
        "mldsa65_signature_algorithm_without_parameters": item["signature_algorithm"] == (OID_ML_DSA_65, True),
        "unsigned_attributes_omitted": not item["has_unsigned_attrs"],
    }
    return {"valid": all(checks.values()), "checks": checks}


def verify_raw_signature(openssl: str, public_key: Path, data: bytes) -> bool:
    item = inspect_signed_object(data)
    with tempfile.TemporaryDirectory(prefix="pqc-rpki-cms-verify-") as name:
        directory = Path(name)
        message = directory / "signed-attrs.der"
        signature = directory / "signature.bin"
        message.write_bytes(item["signed_attrs_der"])
        signature.write_bytes(item["signature"])
        process = subprocess.run(
            [openssl, "pkeyutl", "-verify", "-rawin", "-pubin", "-inkey", str(public_key),
             "-in", str(message), "-sigfile", str(signature)],
            capture_output=True, text=True,
        )
        return process.returncode == 0
