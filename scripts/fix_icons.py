import re

# 1. Update classroom.html
html_path = 'frontend/classroom.html'
with open(html_path, 'r') as f:
    html = f.read()

html = html.replace('class="controls-bar"', 'class="bottom-controls"')
html = html.replace('class="ctrl-btn"', 'class="control-btn"')
html = html.replace('class="ctrl-btn ', 'class="control-btn ')
html = html.replace('class="ctrl-divider"', 'class="control-divider"')

with open(html_path, 'w') as f:
    f.write(html)

# 2. Append CSS for dividers and danger button
css_path = 'frontend/css/styles.css'
css_append = """
.control-divider {
    width: 1px;
    height: 32px;
    background: rgba(255,255,255,0.1);
}

.control-btn.danger {
    background: rgba(244, 63, 94, 0.15);
    color: var(--accent-rose);
    border: 1px solid rgba(244, 63, 94, 0.3);
}
.control-btn.danger:hover {
    background: var(--accent-rose);
    color: white;
}
"""

with open(css_path, 'a') as f:
    f.write("\n" + css_append)

print("Icons fixed.")
