with open('frontend/index.html', 'r') as f:
    content = f.read()

# Make the set password button have the gradient too
content = content.replace(
    'editBtn = `<button class="btn btn-ghost" style="flex:1;background:rgba(255,255,255,0.05);color:var(--text-secondary);border:1px dashed rgba(255,255,255,0.2)"',
    'editBtn = `<button class="btn" style="flex:1;background:linear-gradient(135deg, var(--accent-fuchsia), var(--accent-indigo));color:white;border:none;"'
)

with open('frontend/index.html', 'w') as f:
    f.write(content)
