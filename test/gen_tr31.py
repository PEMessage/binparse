#!/usr/bin/env python3
"""Generate test data for ``binparser -s tr31``.

A TR-31 / X9.143 version-B key block: ASCII header (16 chars), one optional
block, hex-encoded payload and an 8-byte (16-char) CMAC authenticator.
"""

import sys

# --- One optional block: ID + Len + Data (all ASCII, len in hex chars) ---
opt_id = "KS"
opt_data = "00604B120F9738"
opt_block = opt_id + f"{len(opt_id) + 2 + len(opt_data):02X}" + opt_data
opt_count = 1

# --- Payload + authenticator (hex text) ---
payload = "F" * 48          # 48 hex chars of ciphertext
authenticator = "0" * 16    # version B → 8-byte MAC → 16 hex chars

header_wo_len = (
    "B"       # version_id
    "XXXX"    # length placeholder
    "B0"      # key_usage
    "T"       # algorithm (TDES)
    "X"       # mode_of_use
    "12"      # key_version
    "S"       # exportability
    f"{opt_count:02d}"  # opt_blocks_count
    "0"       # key_context
    "0"       # reserved
)

body = opt_block + payload + authenticator
total = len(header_wo_len) + len(body)
header = header_wo_len.replace("XXXX", f"{total:04d}", 1)

sys.stdout.buffer.write((header + body).encode("ascii"))
