#!/usr/bin/env python3
"""Generate test data for ``binparser -s file``.

    struct header  { uint32_t magic; uint16_t version; uint16_t flags; };   // 8 B
    struct info    { uint32_t width; uint32_t height; uint16_t depth; };    // 10 B
"""

import struct
import sys

sys.stdout.buffer.write(struct.pack(
    "<I H H",
    0xDEADBEEF, 1, 0x0003,   # header
))
sys.stdout.buffer.write(struct.pack(
    "<I I H",
    1920, 1080, 24,          # info
))
