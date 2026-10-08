# Insert SQL Query Reference group only
path = 'DockKubeDesktop/command_specs.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

insertion_point = 684  # Before Schema Design group

# Build the SQL Query Reference group content
sql_lines = [
    '    _g("SQL Query Reference",\n',
    '        ("SELECT All Columns", "psql -U postgres -d {arg} -c \\'SELECT * FROM users;\\'"),\n',
    '        ("SELECT Specific Columns", "psql -U postgres -d {arg} -c \\'SELECT email, username FROM users;\\'"),\n',
    '        ("SELECT With Where", "psql -U postgres -d {arg} -c \\'SELECT * FROM users WHERE status = \\'active\\';\\'"),\n',
    '        ("SELECT With Order", "psql -U postgres -d {arg} -c \\'SELECT * FROM users ORDER BY created_at DESC;\\'"),\n',
    '        ("SELECT With Limit", "psql -U postgres -d {arg} -c \\'SELECT * FROM users LIMIT 10;\\'"),\n',
    '        ("SELECT Distinct", "psql -U postgres -d {arg} -c \\'SELECT DISTINCT status FROM users;\\'"),\n',
    '        ("INSERT Single Row", "psql -U postgres -d {arg} -c \\"INSERT INTO users (username, email) VALUES (\\'john\\', \\'john@example.com\\');\\""),\n',
    '        ("INSERT Multi Row", "psql -U postgres -d {arg} -c \\'INSERT INTO users (username, email) VALUES (\\'a\\', \\'a@b.c\\'), (\\'b\\', \\'b@b.c\\');\\'"),\n',
    '        ("UPDATE Single Row", "psql -U postgres -d {arg} -c \\'UPDATE users SET email = \\'new@x.com\\' WHERE id = 1;\\'"),\n',
    '        ("UPDATE Multiple Columns", "psql -U postgres -d {arg} -c \\'UPDATE users SET email = \\'new@x.com\\', full_name = \\'John\\' WHERE id = 1;\\'"),\n',
    '        ("DELETE Single Row", "psql -U postgres -d {arg} -c \\'DELETE FROM users WHERE id = 1;\\'"),\n',
    '        ("DELETE With Condition", "psql -U postgres -d {arg} -c \\'DELETE FROM users WHERE created_at < NOW() - INTERVAL \\'30 days\\'\\\"\\'),\\n',\n',
    '        ("CREATE Table", "psql -U postgres -c \\'CREATE TABLE products (id SERIAL PRIMARY KEY, name VARCHAR(100), price DECIMAL(10,2));\\'"),\n',
    '        ("ALTER TABLE Add Column", "psql -U postgres -d {arg} -c \\'ALTER TABLE users ADD COLUMN phone VARCHAR(20);\\'"),\n',
    '        ("ALTER TABLE Rename", "psql -U postgres -d {arg} -c \\'ALTER TABLE users RENAME TO customers;\\""),\n',
    '    ),\n'
]

# Fix the problematic line - let me construct it correctly
# The DELETE With Condition line should be:
#         ("DELETE With Condition", "psql -U postgres -d {arg} -c \\'DELETE FROM users WHERE created_at < NOW() - INTERVAL \\'30 days\\'\\\"\\'),\n'

# Let me rebuild the sql_lines with the correct DELETE line
sql_lines = [
    '    _g("SQL Query Reference",\n',
    '        ("SELECT All Columns", "psql -U postgres -d {arg} -c \\'SELECT * FROM users;\\'"),\n',
    '        ("SELECT Specific Columns", "psql -U postgres -d {arg} -c \\'SELECT email, username FROM users;\\'"),\n',
    '        ("SELECT With Where", "psql -U postgres -d {arg} -c \\'SELECT * FROM users WHERE status = \\'active\\';\\'"),\n',
    '        ("SELECT With Order", "psql -U postgres -d {arg} -c \\'SELECT * FROM users ORDER BY created_at DESC;\\'"),\n',
    '        ("SELECT With Limit", "psql -U postgres -d {arg} -c \\'SELECT * FROM users LIMIT 10;\\'"),\n',
    '        ("SELECT Distinct", "psql -U postgres -d {arg} -c \\'SELECT DISTINCT status FROM users;\\'"),\n',
    '        ("INSERT Single Row", "psql -U postgres -d {arg} -c \\"INSERT INTO users (username, email) VALUES (\\'john\\', \\'john@example.com\\');\\""),\n',
    '        ("INSERT Multi Row", "psql -U postgres -d {arg} -c \\'INSERT INTO users (username, email) VALUES (\\'a\\', \\'a@b.c\\'), (\\'b\\', \\'b@b.c\\');\\'"),\n',
    '        ("UPDATE Single Row", "psql -U postgres -d {arg} -c \\'UPDATE users SET email = \\'new@x.com\\' WHERE id = 1;\\'"),\n',
    '        ("UPDATE Multiple Columns", "psql -U postgres -d {arg} -c \\'UPDATE users SET email = \\'new@x.com\\', full_name = \\'John\\' WHERE id = 1;\\'"),\n',
    '        ("DELETE Single Row", "psql -U postgres -d {arg} -c \\'DELETE FROM users WHERE id = 1;\\'"),\n',
    '        ("DELETE With Condition", "psql -U postgres -d {arg} -c \\'DELETE FROM users WHERE created_at < NOW() - INTERVAL \\'30 days\\'\\\"\\'),\\n',\n',
    '        ("CREATE Table", "psql -U postgres -c \\'CREATE TABLE products (id SERIAL PRIMARY KEY, name VARCHAR(100), price DECIMAL(10,2));\\'"),\n',
    '        ("ALTER TABLE Add Column", "psql -U postgres -d {arg} -c \\'ALTER TABLE users ADD COLUMN phone VARCHAR(20);\\'"),\n',
    '        ("ALTER TABLE Rename", "psql -U postgres -d {arg} -c \\'ALTER TABLE users RENAME TO customers;\\""),\n',
    '    ),\n'
]

lines[insertion_point:insertion_point] = sql_lines

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print(f"Inserted SQL Query Reference group: {len(sql_lines)} lines")