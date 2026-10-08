path = r'C:\Users\32813 MHM Hamdhi\Desktop\DocKube\DockKubeDesktop\command_specs.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix line 685: 4 spaces -> 7 spaces
if 'SELECT All Columns' in lines[684]:
    lines[684] = '        ' + lines[684][4:]

# Fix Schema Design group: 5 spaces -> 4 spaces
for i in range(690, 698):
    if '_g' in lines[i]:
        lines[i] = '    ' + lines[i][5:]
        break

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('Fixed')
