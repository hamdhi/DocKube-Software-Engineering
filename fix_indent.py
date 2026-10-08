path = r'C:\Users\32813 MHM Hamdhi\Desktop\DocKube\DockKubeDesktop\command_specs.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix SQL Query Reference group: change item indentation from 4 to 7 spaces
for i in range(685, 691):
    if 'SELECT' in lines[i] and '(' in lines[i]:
        lines[i] = '        ' + lines[i].lstrip()

# Fix end of SQL Query Reference group
for i in range(684, 691):
    if 'SELECT Distinct' in lines[i]:
        lines[i] = '        ' + lines[i].lstrip()
        break

# Fix Schema Design group indent: 5 spaces -> 4 spaces
for i in range(691, 698):
    if '_g' in lines[i] and 'Schema Design' in lines[i]:
        lines[i] = '    ' + lines[i][5:]
        break

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('Done')
