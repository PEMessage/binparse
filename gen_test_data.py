#!/usr/bin/env python3
"""Generate sample binary data for testing the struct parser.

Writes *count* Entry records to stdout.

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
    ap = argparse.ArgumentParser(description="Generate test binary data")
    ap.add_argument(
        "-n", "--count", type=int, default=5,
        help="Number of records (default: 5)",
    )
    ap.add_argument(
        "--partial", action="store_true",
        help="Append an incomplete trailing record to test partial-input handling",
    )
    ap.add_argument(
        "-s", "--seed", type=int, default=0,
        help="Base id seed (default: 0)",
    )
    args = ap.parse_args()

    base_ts = 1700000000  # 2023-11-14T22:13:20Z
    for i in range(args.count):
        rec = struct.pack(
            "<II H H B 3s",
            args.seed + i * 1000,         # id
            base_ts + i * 3600,           # timestamp
            i % 3,                        # type
            i * 42,                       # value
            (i | 0x80) & 0xFF,            # flag
            bytes([(i + 1) & 0xFF, (i + 2) & 0xFF, (i + 3) & 0xFF]),
        )
        sys.stdout.buffer.write(rec)

    if args.partial:
        sys.stdout.buffer.write(b"\x64\x00\x00\x00\xc8\x00\x00\x00\x01\x00\x2a")


if __name__ == "__main__":
    main()
