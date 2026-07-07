#!/usr/bin/env python3
"""Generate test data for ``binparser -s struct``.

Entry (16 bytes, little-endian)::

    uint32_t id;
    uint32_t timestamp;
    uint16_t type;
    uint16_t value;
    uint8_t  flag;
    uint8_t  reserved[3];
"""

import argparse
import struct
import sys


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate binary data for -s struct")
    ap.add_argument("-n", type=int, default=5, help="Number of records (default: 5)")
    ap.add_argument("--partial", action="store_true", help="Append truncated trailing record")
    args = ap.parse_args()

    base_ts = 1700000000
    for i in range(args.n):
        rec = struct.pack(
            "<II H H B 3s",
            i * 1000,
            base_ts + i * 3600,
            i % 3,
            i * 42,
            (i | 0x80) & 0xFF,
            bytes([(i + 1) & 0xFF, (i + 2) & 0xFF, (i + 3) & 0xFF]),
        )
        sys.stdout.buffer.write(rec)

    if args.partial:
        sys.stdout.buffer.write(b"\x64\x00\x00\x00\xc8\x00\x00\x00\x01\x00\x2a")


if __name__ == "__main__":
    main()
