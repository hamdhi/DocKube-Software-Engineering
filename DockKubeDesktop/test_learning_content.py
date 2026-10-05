"""Summarise every chapter and confirm all tables parse."""
import learning
import learning_index as index

total_blocks = total_tables = total_rows = 0

for name, body in index.CHAPTERS:
    blocks = learning.parse_content(body)
    tables = [b for b in blocks if b.kind == "table"]
    rows = sum(len(t.rows) for t in tables)
    total_blocks += len(blocks)
    total_tables += len(tables)
    total_rows += rows
    print(f"{name:36s} {len(blocks):4d} blocks  {len(tables):2d} tables  {rows:3d} rows")

intro_blocks = learning.parse_content(index.INTRO)
intro_tables = [b for b in intro_blocks if b.kind == "table"]
print(f"{'INTRO':36s} {len(intro_blocks):4d} blocks  {len(intro_tables):2d} tables")

print(f"\nTOTAL {total_blocks} blocks, {total_tables} tables, {total_rows} table rows")
print(f"Chapters: {len(index.CHAPTERS)}")

# Nothing should render as a raw pipe row any more.
leftovers = []
for name, body in index.CHAPTERS + [("INTRO", index.INTRO)]:
    for block in learning.parse_content(body):
        if block.kind == "p" and block.text.startswith("|"):
            leftovers.append((name, block.text[:50]))
print("raw pipe paragraphs left:", len(leftovers))
for name, text in leftovers[:5]:
    print("   ", name, text)