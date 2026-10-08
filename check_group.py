path = r'C:\Users\32813 MHM Hamdhi\Desktop\DocKube\DockKubeDesktop\command_specs.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find MongoDB group start
for i, line in enumerate(lines):
    if '\"MongoDB\"' in line and '_g' in line:
        print(f'MongoDB group starts at line {i+1}')
        for j in range(i, min(i+12, len(lines))):
            print(f'  {j+1}: {repr(lines[j])}')
        break
