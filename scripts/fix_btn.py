with open('frontend/classroom.html', 'r') as f:
    content = f.read()

content = content.replace('<button class="btn btn-outline" id="btn-change-pwd">', '<button class="btn" style="background: linear-gradient(135deg, var(--accent-fuchsia), var(--accent-indigo)); color: white; border: none;" id="btn-change-pwd">')

with open('frontend/classroom.html', 'w') as f:
    f.write(content)
