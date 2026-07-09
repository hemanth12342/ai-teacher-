with open('frontend/index.html', 'r') as f:
    content = f.read()

content = content.replace("${room.has_password ? 'Join →' : '🔓 Open'}", 'Join →')

with open('frontend/index.html', 'w') as f:
    f.write(content)
