import io

path = 'DockKubeDesktop/command_specs.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the exact insertion point: after MongoDB group ends (line 683)
# MongoDB group ends at line 683: "        (\"List Indexes\", \"mongosh {arg} --eval 'db.orders.getIndexes()'")),\n"
# Schema Design group starts at line 684: "    _g(\"Schema Design and Normalisation\",\n"

insertion_point = 684  # Insert before Schema Design group

new_groups = [
    "    _g(\"SQL Query Reference\",\n",
    "        (\"SELECT All Columns\", \"psql -U postgres -d {arg} -c 'SELECT * FROM users;'\"),\n",
    "        (\"SELECT Specific Columns\", \"psql -U postgres -d {arg} -c 'SELECT email, username FROM users;'\"),\n",
    "        (\"SELECT With Where\", \"psql -U postgres -d {arg} -c 'SELECT * FROM users WHERE status = 'active';'\"),\n",
    "        (\"SELECT With Order\", \"psql -U postgres -d {arg} -c 'SELECT * FROM users ORDER BY created_at DESC;'\"),\n",
    "        (\"SELECT With Limit\", \"psql -U postgres -d {arg} -c 'SELECT * FROM users LIMIT 10;'\"),\n",
    "        (\"SELECT Distinct\", \"psql -U postgres -d {arg} -c 'SELECT DISTINCT status FROM users;'\"),\n",
    "        (\"INSERT Single Row\", \"psql -U postgres -d {arg} -c \\\"INSERT INTO users (username, email) VALUES ('john', 'john@example.com');\\\"\"),\n",
    "        (\"INSERT Multi Row\", \"psql -U postgres -d {arg} -c 'INSERT INTO users (username, email) VALUES (''a'', ''a@b.c''), (''b'', ''b@b.c'');'\"),\n",
    "        (\"UPDATE Single Row\", \"psql -U postgres -d {arg} -c 'UPDATE users SET email = ''new@x.com'' WHERE id = 1;'\"),\n",
    "        (\"UPDATE Multiple Columns\", \"psql -U postgres -d {arg} -c 'UPDATE users SET email = ''new@x.com'', full_name = ''John'' WHERE id = 1;'\"),\n",
    "        (\"DELETE Single Row\", \"psql -U postgres -d {arg} -c 'DELETE FROM users WHERE id = 1;'\"),\n",
    "        (\"DELETE With Condition\", \"psql -U postgres -d {arg} -c 'DELETE FROM users WHERE created_at < NOW() - INTERVAL '30 days';'\"),\n",
    "        (\"CREATE Table\", \"psql -U postgres -c 'CREATE TABLE products (id SERIAL PRIMARY KEY, name VARCHAR(100), price DECIMAL(10,2));'\"),\n",
    "        (\"ALTER TABLE Add Column\", \"psql -U postgres -d {arg} -c 'ALTER TABLE users ADD COLUMN phone VARCHAR(20);'\"),\n",
    "        (\"ALTER TABLE Rename\", \"psql -U postgres -d {arg} -c 'ALTER TABLE users RENAME TO customers;'"),\n",
    "    ),\n",
    "    _g(\"MongoDB Query Operators\",\n",
    "        (\"Find All Documents\", \"mongosh {arg} --eval 'db.orders.find();'\"),\n",
    "        (\"Find With Filter\", \"mongosh {arg} --eval 'db.orders.find({status: E'paid'});'\"),\n",
    "        (\"Find With Sort\", \"mongosh {arg} --eval 'db.orders.find().sort({{createdAt: -1}}).limit(5);'\"),\n",
    "        (\"Count Documents\", \"mongosh {arg} --eval 'db.orders.countDocuments({{status: E'paid'}});'\"),\n",
    "    ),\n"
]

# Insert the new groups
lines[insertion_point:insertion_point] = new_groups

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print(f"Inserted {len(new_groups)} lines at position {insertion_point}")
