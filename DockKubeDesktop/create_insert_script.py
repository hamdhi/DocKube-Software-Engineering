# This script will create the actual insertion script
script_content = '''# Build the content to insert
content_to_insert = []

# SQL Query Reference group
content_to_insert.append('    _g("SQL Query Reference",\\n')
content_to_insert.append('        ("SELECT All Columns", "psql -U postgres -d {arg} -c \\'SELECT * FROM users;\\'"),\\n')
content_to_insert.append('        ("SELECT Specific Columns", "psql -U postgres -d {arg} -c \\'SELECT email, username FROM users;\\'"),\\n')
content_to_insert.append('        ("SELECT With Where", "psql -U postgres -d {arg} -c \\'SELECT * FROM users WHERE status = \\'active\\';\\'"),\\n')
content_to_insert.append('        ("SELECT With Order", "psql -U postgres -d {arg} -c \\'SELECT * FROM users ORDER BY created_at DESC;\\'"),\\n')
content_to_insert.append('        ("SELECT With Limit", "psql -U postgres -d {arg} -c \\'SELECT * FROM users LIMIT 10;\\'"),\\n')
content_to_insert.append('        ("SELECT Distinct", "psql -U postgres -d {arg} -c \\'SELECT DISTINCT status FROM users;\\'"),\\n')
content_to_insert.append('        ("INSERT Single Row", "psql -U postgres -d {arg} -c \\"INSERT INTO users (username, email) VALUES (\\'john\\', \\'john@example.com\\');\\""),\\n')
content_to_insert.append('        ("INSERT Multi Row", "psql -U postgres -d {arg} -c \\'INSERT INTO users (username, email) VALUES (\\'a\\', \\'a@b.c\\'), (\\'b\\', \\'b@b.c\\');\\'"),\\n')
content_to_insert.append('        ("UPDATE Single Row", "psql -U postgres -d {arg} -c \\'UPDATE users SET email = \\'new@x.com\\' WHERE id = 1;\\'"),\\n')
content_to_insert.append('        ("UPDATE Multiple Columns", "psql -U postgres -d {arg} -c \\'UPDATE users SET email = \\'new@x.com\\', full_name = \\'John\\' WHERE id = 1;\\'"),\\n')
content_to_insert.append('        ("DELETE Single Row", "psql -U postgres -d {arg} -c \\'DELETE FROM users WHERE id = 1;\\'"),\\n')
content_to_insert.append('        ("DELETE With Condition", "psql -U postgres -d {arg} -c \\'DELETE FROM users WHERE created_at < NOW() - INTERVAL \\'30 days\\';\\""),\\n')
content_to_insert.append('        ("CREATE Table", "psql -U postgres -c \\'CREATE TABLE products (id SERIAL PRIMARY KEY, name VARCHAR(100), price DECIMAL(10,2));\\'"),\\n')
content_to_insert.append('        ("ALTER TABLE Add Column", "psql -U postgres -d {arg} -c \\'ALTER TABLE users ADD COLUMN phone VARCHAR(20);\\'"),\\n')
content_to_insert.append('        ("ALTER TABLE Rename", "psql -U postgres -d {arg} -c \\'ALTER TABLE users RENAME TO customers;\\""),\\n')
content_to_insert.append('    ),\\n')

# MongoDB Query Operators group
content_to_insert.append('    _g("MongoDB Query Operators",\\n')
content_to_insert.append('        ("Find All Documents", "mongosh {arg} --eval \\'db.orders.find();\\'"),\\n')
content_to_insert.append('        ("Find With Filter", "mongosh {arg} --eval \\'db.orders.find({status: E\\'paid\\'});\\'"),\\n')
content_to_insert.append('        ("Find With Sort", "mongosh {arg} --eval \\'db.orders.find().sort({{createdAt: -1}}).limit(5);\\'"),\\n')
content_to_insert.append('        ("Count Documents", "mongosh {arg} --eval \\'db.orders.countDocuments({{status: E\\'paid\\'}});\\'"),\\n')
content_to_insert.append('    ),\\n')

# Now insert the content
path = 'DockKubeDesktop/command_specs.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

insertion_point = 684  # Before Schema Design group

lines[insertion_point:insertion_point] = content_to_insert

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print(f"Inserted {len(content_to_insert)} lines")
'''

with open('DockKubeDesktop/build_and_insert.py', 'w', encoding='utf-8') as f:
    f.write(script_content)

print("Created build_and_insert.py")