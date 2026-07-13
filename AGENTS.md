# AGENTS.md — binparser Development Notes

## Best Learning How to Use Hachoir

The best way to learn hachoir is from its **existing parsers**.  Locate the
source directory first:

```bash
uv run --with hachoir python3 -c "import hachoir.parser ; print(hachoir.parser.__path__)"
```

Then browse the parsers (e.g. `png.py`, `gif.py`, `elf.py`) to see real-world
usage patterns — field definitions, `createFields()`, endian handling, and
conditional parsing.

## Toolchain: `uv run --script`

The main entry point `binparser` is a **PEP 723 inline-script** (the `/// script`
header block).  uv reads this metadata, creates an ephemeral venv, and
auto-installs dependencies — no `pyproject.toml` or manual `pip install` needed.

```bash
# Add a dependency (writes into the /// script header block)
uv add --script binparser hachoir

# Run (uv manages venv + deps automatically)
uv run --script binparser -- -s demoA < data.bin

# Experiment in isolation (does not touch project files)
uv run --with hachoir python -c "..."
```

## How to Explore Hachoir's Lesser-Known APIs

### Rule: Always Verify in Isolation First

When you need to understand hachoir API behaviour (e.g. the address unit for
`readBytes`, or the semantics of `is_field_set`), **use
`uv run --with hachoir python -c "..."` to build a minimal reproduction in
memory**.  Confirm the behaviour before touching `binparser`.

This avoids the cycle of: edit the main file → run → error → edit again.

### Example: `is_field_set` vs `isinstance`

`_extract_fields` originally used `isinstance(field, (UInt32, UInt16, UInt8,
RawBytes))` to distinguish containers from leaf nodes — every new field type
meant updating that tuple.

An isolated experiment showed that hachoir's `FieldSet` has an `is_field_set`
attribute: `True` for containers, `False` for leaves (including autofix
raw/padding fields):

```bash
uv run --with hachoir python -c "
...
for f in field:
    print(f.name, f.is_field_set)
"
```

The check was then replaced with `getattr(field, 'is_field_set', False)`,
eliminating the type whitelist entirely.

## Workflow Summary

1. **`uv run --with <pkg> python -c "..."`** — experiment with the API in isolation
2. **After confirming behaviour** — edit the corresponding logic in `binparser`
3. **`./test.sh`** — run the full test suite (3 parsers × multiple options)

## File Layout

```
binparser          # main entry point (PEP 723 inline-script)
test/
  gen_demoA.py      # generates test data for the demoA struct
  gen_demoB.py      # generates test data for the demoB struct
  gen_asn1.py       # generates ASN.1 BER/DER test data
test.sh             # quick regression suite
```

---

## Common Hachoir Patterns

### Field Types (from `hachoir.field`)

```python
from hachoir.field import (
    # Integers
    UInt8, UInt16, UInt32, UInt64,

    # Strings
    String,          # Fixed-length:  String(self, "name", length, "Desc", charset="ASCII")
    CString,         # Null-terminated: CString(self, "name", "Desc", charset="ISO-8859-1")
    PascalString8,   # Length-prefixed (8-bit len)
    PascalString16,  # Length-prefixed (16-bit len)

    # Bits / Bytes
    Bit,             # Single bit:   Bit(self, "flag")
    Bits,            # Multi-bit:    Bits(self, "field", 3)
    Bytes,           # Fixed bytes:  Bytes(self, "id", 8, "Magic")
    RawBytes,        # Opaque dump:  RawBytes(self, "data", size)

    # Padding
    NullBits,        # NullBits(self, "reserved", 5)
    NullBytes,       # NullBytes(self, "padding", 1)
    PaddingBits, PaddingBytes,

    # Containers
    FieldSet,        # Reusable group of fields
    Parser,          # Root parser (aka HachoirParser)

    # Wrappers
    Enum,            # Enum(UInt8(self, "type"), {0: "none", 1: "meter"})
    SubFile,         # Encapsulate embedded data segment
    CompressedField, # Decompress inline

    # Misc
    TimeDateMSDOS32, # DOS timestamp
    ParserError,     # raise ParserError("reason")
)
```

### Enum Pattern — the Most Common Wrapper

Every parser uses `Enum` to map integer codes to human-readable labels. Works
with any integer type: `UInt8`, `UInt16`, `UInt32`, `UInt64`, `Bits`.

```python
COMPRESSION_METHOD = {
    0: "no compression",
    8: "Deflate",
    9: "Deflate64",
}
yield Enum(UInt16(self, "compression"), COMPRESSION_METHOD)

# Also works with Bits:
yield Enum(Bits(self, "table_class", 4), {0: "DC", 1: "AC"})
```

### textHandler — Display Integer as Hex

```python
from hachoir.core.text_handler import textHandler, hexadecimal
yield textHandler(UInt32(self, "crc32"), hexadecimal)
```

### FieldSet — the Reusable Block Pattern

```python
class MyChunk(FieldSet):
    def createFields(self):
        yield UInt32(self, "size")
        yield String(self, "tag", 4, charset="ASCII")
        if self["size"].value:
            yield RawBytes(self, "data", self["size"].value)

    def createDescription(self):           # optional human-readable summary
        return "Chunk: %s" % self["tag"].display
```

### Parser — the Root Parser

```python
from hachoir.parser import Parser
from hachoir.core.endian import LITTLE_ENDIAN

class MyFile(Parser):
    endian = LITTLE_ENDIAN
    PARSER_TAGS = {
        "id": "myformat",
        "category": "misc",
        "file_ext": ("ext",),
        "mime": ("application/x-myformat",),
        "magic": ((b"\x89MAGIC", 0),),
        "min_size": 16 * 8,              # in bits!
        "description": "My file format",
    }

    def validate(self):
        # Return True if valid, or error string
        if self.stream.readBytes(0, 4) != b"MAGI":
            return "Invalid magic"
        return True

    def createFields(self):
        while not self.eof:
            yield MyChunk(self, "chunk[]")   # [] suffix = array index

    def createDescription(self):
        return "MyFile: %d chunks" % (len(self.array("chunk")))
```

### Conditional Parsing — Gate on Field Value

```python
if self["has_local_map"].value:
    nb_color = 1 << (1 + self["size_local_map"].value)
    yield PaletteRGB(self, "local_map", nb_color)
```

### Looping with Array Indices — the `[]` Convention

```python
# Fixed number of items:
for i in range(nb_color):
    yield RGB(self, "color[]")           # becomes color[0], color[1], ...

# Until EOF or sentinel:
while not self.eof:
    yield Chunk(self, "chunk[]")         # becomes chunk[0], chunk[1], ...
```

### Size Arithmetic — Everything Is in Bits

```python
# FieldSet has:
self.size            # total expected size in bits
self.current_size    # bytes yielded so far (bits)
self.eof             # .current_size >= .size

# Child field size in bits:
self["header"].size // 8     # size in bytes
self["data"].value           # .value for integers

# Assign _size explicitly (in bits) when known ahead:
self._size = (size_bytes + 3 * 4) * 8
```

### Peeking the Stream (Non-Advancing)

```python
# readBytes(address_in_bits, count_in_bytes)
first_byte = self.stream.readBytes(self.absolute_address, 1)[0]

# readBits(address_in_bits, count_in_bits, endian)
header = self.stream.readBits(addr, 32, self.endian)
```

### Error Handling & Early Exit

```python
raise ParserError("Invalid chunk: expected 0x01, got 0x%02X" % val)

# Early return from createFields() generator:
if self["size"].value == 0:
    return
```
