import re, json, os

def markdown_to_html(md):
    # Simple conversion: headings, lists, code fences, tables
    html = md
    # headings ##, ### etc.
    html = re.sub(r'(?m)^#{6}\s*(.*)', r'<h6>\1</h6>', html)
    html = re.sub(r'(?m)^#{5}\s*(.*)', r'<h5>\1</h5>', html)
    html = re.sub(r'(?m)^#{4}\s*(.*)', r'<h4>\1</h4>', html)
    html = re.sub(r'(?m)^#{3}\s*(.*)', r'<h3>\1</h3>', html)
    html = re.sub(r'(?m)^#{2}\s*(.*)', r'<h2>\1</h2>', html)
    html = re.sub(r'(?m)^#\s*(.*)', r'<h1>\1</h1>', html)
    # unordered lists
    html = re.sub(r'(?m)^[\*\-]\s+(.*)', r'<li>\1</li>', html)
    # wrap consecutive li in ul
    html = re.sub(r'(?s)((?:<li>.*?</li>\s*)+)', lambda m: f'<ul>{m.group(0)}</ul>', html)
    # ordered lists
    html = re.sub(r'(?m)^\d+\.\s+(.*)', r'<li>\1</li>', html)
    html = re.sub(r'(?s)((?:<li>.*?</li>\s*)+)', lambda m: f'<ol>{m.group(0)}</ol>', html)
    # code fences ```
    html = re.sub(r'(?s)```python\n(.*?)```', r'<pre><code style="font-family:Courier New;">\1</code></pre>', html)
    html = re.sub(r'(?s)```\n(.*?)```', r'<pre><code style="font-family:Courier New;">\1</code></pre>', html)
    # tables markdown to html simple (not handling complex)
    # replace pipe tables naive
    return html

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    # find docs dict start and end (simple heuristic)
    pattern = r'self\.docs\s*=\s*\{(.*?)\n\s*\}\n'
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        print('Docs dict not found')
        return
    inner = match.group(1)
    # split entries by commas not within quotes (simple)
    entries = re.finditer(r'\"([^\"]+)\":\s*\"\"\"(.*??)\"\"\"', inner, re.DOTALL)
    new_entries = []
    for e in entries:
        key = e.group(1)
        md = e.group(2)
        html = markdown_to_html(md)
        # escape triple quotes
        html_escaped = html.replace('"', '\\"')
        new_entries.append(f'"{key}": """{html}"""')
    new_dict = ',\n'.join(new_entries)
    new_content = re.sub(pattern, f'self.docs = {{{new_dict}\n}}\n', content, flags=re.DOTALL)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('Conversion done')

if __name__ == '__main__':
    process_file(os.path.abspath('app.py'))
