path = 'DockKubeDesktop/command_specs.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Insert after MongoDB group (before Schema Design group)
insertion_point = 684

# Simple test - just add one line
new_lines = ['    # INSERTED LINE\n']

lines[insertion_point:insertion_point] = new_lines

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print(f"Inserted {len(new_lines)} lines")