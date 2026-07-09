with open('frontend/index.html', 'r') as f:
    content = f.read()

content = content.replace('!!room.password', '!!room.has_password')
content = content.replace('room.password ?', 'room.has_password ?')

with open('frontend/index.html', 'w') as f:
    f.write(content)
