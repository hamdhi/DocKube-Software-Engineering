"""Parser tests: HTML tables, markdown pipes, edge cases."""
import learning

MD_TABLE = """Some intro text.

| CIDR | Mask | Usable hosts |
|------|------|--------------|
| `/32` | 255.255.255.255 | 1 |
| `/24` | 255.255.255.0 | 254 |
| `/16` | 255.255.0.0 | 65534 |

After text.
"""

HTML_TABLE = """<h1>Chapter</h1>
<p>Intro paragraph.</p>
<table>
<tr><th>Layer</th><th>Device</th></tr>
<tr><td>2</td><td>Switch</td></tr>
<tr><td>3</td><td>Router</td></tr>
</table>
<p>Closing.</p>
"""

MIXED = """<h2>Real HTML</h2>
<table>
<tr><th>A</th><th>B</th></tr>
<tr><td>1</td><td>2</td></tr>
</table>

| C | D |
|---|---|
| 3 | 4 |
"""

print("=== markdown pipe table ===")
for block in learning.parse_content(MD_TABLE):
    if block.kind == "table":
        print("table rows:", block.rows)
        assert block.rows[0] == ["CIDR", "Mask", "Usable hosts"]
        assert block.rows[1] == ["/32", "255.255.255.255", "1"]
        assert len(block.rows) == 4, "header + 3 data rows, separator dropped"
    elif block.kind == "p":
        print("p:", repr(block.text))

print("\n=== html table ===")
tables = [b for b in learning.parse_content(HTML_TABLE) if b.kind == "table"]
assert len(tables) == 1, f"expected 1 table, got {len(tables)}"
assert tables[0].rows[0] == ["Layer", "Device"]
assert tables[0].rows[2] == ["3", "Router"]
print("rows:", tables[0].rows)

print("\n=== headings / code / bullets ===")
sample = """<h1>Title</h1><h2>Sub</h2><h3>Deep</h3>
<ul><li>One</li><li>Two</li></ul>
<pre><code>kubectl get pods</code></pre>
<hr/>
"""
kinds = [(b.kind, b.text[:20]) for b in learning.parse_content(sample)]
print(kinds)
assert [k for k, _ in kinds] == ["title", "h2", "h3", "bullet", "bullet", "code", "rule"]

print("\n=== mixed html + markdown in one doc ===")
mixed = [b for b in learning.parse_content(MIXED) if b.kind == "table"]
print("tables:", len(mixed))
for t in mixed:
    print("  ", t.rows)
assert len(mixed) == 2, "both an HTML and a markdown table must render"

print("\n=== edge cases ===")
print("empty ->", learning.parse_content(""))
print("no pipes ->", len(learning.parse_content("| lone | line |")))
single = [b for b in learning.parse_content("| one | two |") if b.kind == "table"]
print("single-line pipe (not a table) ->", single)
ragged = "| A | B | C |\n|---|---|\n| 1 | 2 |\n"
print("ragged rows ->", [b.rows for b in learning.parse_content(ragged) if b.kind == "table"])
print("entities ->", [b.text for b in learning.parse_content("<p>a &amp; b &lt;tag&gt;</p>")])
print("nested markup ->", [b.text for b in learning.parse_content("<p><strong>bold</strong> and <code>code</code></p>")])

print("\n=== unclosed tag does not crash ===")
print(learning.parse_content("<p>text <strong>bold"))

print("\nPARSER TESTS PASSED")