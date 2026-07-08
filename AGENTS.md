# AGENTS.md — binparser Development Notes

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

### Example: Discovering That `readBytes` Addresses Are in Bits

ASN.1 parsing requires peeking at the leading byte to determine how many bytes
the tag and length fields occupy.  Hachoir's `createFields()` is a generator;
calling `self.stream.readBytes()` inside it does **not** advance the parser's
position tracker — it is a non-destructive peek.

However, the initial code `readBytes(byte_pos, 1)` passed a byte offset where
hachoir expected a bit address, causing the internal error
`"TODO: handle non-byte-aligned data"` and triggering an autofix that swallowed
the entire TLV as raw bytes.

The following isolated experiment revealed the correct address unit:

```bash
uv run --with hachoir python -c "
from hachoir.stream import StringInputStream
s = StringInputStream(b'Hello')
print(s.readBytes(0, 1))   # b'H'   ← bit 0
print(s.readBytes(8, 1))   # b'e'   ← bit 8 = byte 1
print(s.readBytes(1, 1))   # error  ← bit 1 is not byte-aligned
"
```

Conclusion: `readBytes(address, count)` expects `address` in **bits**.
Therefore the correct peek pattern is:

```python
bit_pos = self.absolute_address + self.current_size  # already in bits
tag0 = self.stream.readBytes(bit_pos, 1)[0]
```

Only after confirming this did the peek logic go into `ASN1TLV.createFields()`.

### Another Example: `is_field_set` vs `isinstance`

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
