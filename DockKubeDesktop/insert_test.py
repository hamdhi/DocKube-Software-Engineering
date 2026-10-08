path = 'DockKubeDesktop/command_specs.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

insertion_point = 684

new_lines = [
    '    _g("TEST GROUP",\n',
    '        ("TEST COMMAND", "echo test")\n',
    '    ),\n'
]

lines[insertion_point:insertion_point] = new_lines

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print(f"Inserted TEST GROUP: {len(new_lines)} lines")