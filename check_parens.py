path = r'C:\Users\32813 MHM Hamdhi\Desktop\DocKube\DockKubeDesktop\command_specs.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the DATABASE_ADMIN_GROUPS section
start = None
end = None
for i, line in enumerate(lines):
    if 'DATABASE_ADMIN_GROUPS' in line:
        start = i
    if start is not None and end is None and line.strip() == ']' and 'Windows' not in ''.join(lines[i:i+3]):
        end = i
        break

print(f'Section from line {start+1} to {end+1}')
print('Counting parentheses in the section...')
depth = 0
for i in range(start, end+1):
    line = lines[i]
    # Count parens in the line (ignoring strings)
    for ch in line:
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
    if depth < 0:
        print(f'  ERROR: Negative depth at line {i+1}: {repr(line)}')
        depth = 0
    print(f'{i+1}: depth={depth}  {repr(line[:60])}')