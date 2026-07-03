from __future__ import annotations


def length(value: int) -> bytes:
    if value < 0:
        raise ValueError("DER length must be non-negative")
    if value < 128:
        return bytes([value])
    encoded = value.to_bytes((value.bit_length() + 7) // 8, "big")
    return bytes([0x80 | len(encoded)]) + encoded


def tlv(tag: int, value: bytes) -> bytes:
    return bytes([tag]) + length(len(value)) + value


def sequence(*values: bytes) -> bytes:
    return tlv(0x30, b"".join(values))


def set_of(*values: bytes) -> bytes:
    return tlv(0x31, b"".join(sorted(values)))


def integer(value: int) -> bytes:
    if value < 0:
        raise ValueError("negative INTEGER is not supported")
    if value == 0:
        encoded = b"\x00"
    else:
        encoded = value.to_bytes((value.bit_length() + 7) // 8, "big")
        if encoded[0] & 0x80:
            encoded = b"\x00" + encoded
    return tlv(0x02, encoded)


def octet_string(value: bytes) -> bytes:
    return tlv(0x04, value)


def bit_string(value: bytes, unused_bits: int = 0) -> bytes:
    if not 0 <= unused_bits <= 7:
        raise ValueError("unused bit count must be between 0 and 7")
    return tlv(0x03, bytes([unused_bits]) + value)


def ia5_string(value: str) -> bytes:
    return tlv(0x16, value.encode("ascii"))


def generalized_time(value: str) -> bytes:
    return tlv(0x18, value.encode("ascii"))


def utc_time(value: str) -> bytes:
    return tlv(0x17, value.encode("ascii"))


def null() -> bytes:
    return b"\x05\x00"


def object_identifier(value: str) -> bytes:
    arcs = [int(part) for part in value.split(".")]
    if len(arcs) < 2 or arcs[0] > 2 or arcs[1] > 39:
        raise ValueError(f"invalid OID: {value}")
    encoded = bytes([arcs[0] * 40 + arcs[1]])
    for arc in arcs[2:]:
        if arc < 0:
            raise ValueError(f"invalid OID arc: {value}")
        parts = [arc & 0x7F]
        arc >>= 7
        while arc:
            parts.append(0x80 | (arc & 0x7F))
            arc >>= 7
        encoded += bytes(reversed(parts))
    return tlv(0x06, encoded)


def algorithm_identifier(oid: str, *, include_null: bool = False) -> bytes:
    return sequence(object_identifier(oid), null() if include_null else b"")
