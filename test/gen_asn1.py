#!/usr/bin/env python3
"""Generate test data for ``binparser -s asn1``.

ASN.1 BER/DER TLV records with mixed short/long-form length
and single/multi-byte tags.
"""

import struct
import sys

records: list[tuple[int, bytes]] = [
    # Tag < 31, short length
    (0x02, b"\x01\x02\x03"),                    # INTEGER, 3 bytes
    (0x04, b"Hello"),                           # OCTET STRING, 5 bytes
    (0x05, b""),                                # NULL, 0 bytes

    # Tag < 31, long-form length (>= 128 bytes)
    (0x04, b"X" * 200),                         # OCTET STRING, 200 bytes → 0x81 0xC8

    # High tag number (>= 31) → multi-byte tag encoding
    # 0x1F | 0x20 = 0x3F (class=0, constructed=0, tag=0x1F=high-tag-marker)
    # Then 0x81 0x00 = tag = 0x80
    (0x80, b"hi_tag"),                          # tag=128, short length
]

for tag, value in records:
    # Tag byte
    if tag < 31:
        sys.stdout.buffer.write(bytes([tag]))
    else:
        # High-tag-number encoding: first byte = (class << 6) | (0 << 5) | 0x1F
        # then base-128 encoding of remaining tag value
        tag0 = (tag & 0xFFFFFFC0) | 0x1F  # preserve class bits, set tag=0x1F
        rest = tag & 0x3F  # actual tag number (but we already encoded differently above)

        # Actually for simplicity: just encode the tag properly
        # tag = 0x80 → bytes: 0x1F, 0x81, 0x00
        # (class=0, tag bits: 0x80 = 0b10000000 → base-128: high bit set on first byte)
        # Wait, let me recalculate:
        # tag 0x80 = 128 = 0b10000000
        # base-128: need 2 bytes: [0x81, 0x00]
        # 0x81 = 1_0000001 ← bit7=1 (more), bits6-0 = 1
        # 0x00 = 0_0000000 ← bit7=0 (stop), bits6-0 = 0
        # Decoded: 1 << 7 | 0 = 128 ✓
        sys.stdout.buffer.write(bytes([0x1F, 0x81, 0x00]))

    # Length
    n = len(value)
    if n < 128:
        sys.stdout.buffer.write(bytes([n]))
    else:
        # Long form: first byte = 0x80 | num_len_bytes, then length bytes
        len_bytes = struct.pack(">I", n).lstrip(b"\x00") or b"\x00"
        sys.stdout.buffer.write(bytes([0x80 | len(len_bytes)]))
        sys.stdout.buffer.write(len_bytes)

    sys.stdout.buffer.write(value)
