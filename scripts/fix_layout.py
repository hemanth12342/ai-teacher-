with open('frontend/css/styles.css', 'r') as f:
    content = f.read()

# Fix main-area
if 'min-height: 0;' not in content[content.find('.main-area {'):]:
    content = content.replace(
        '.main-area {\n    grid-area: main;',
        '.main-area {\n    grid-area: main;\n    min-height: 0;'
    )

# Fix sidebar
if 'min-height: 0;' not in content[content.find('.sidebar {'):]:
    content = content.replace(
        '.sidebar {\n    grid-area: sidebar;',
        '.sidebar {\n    grid-area: sidebar;\n    min-height: 0;'
    )

# Fix sidebar-panel
if 'min-height: 0;' not in content[content.find('.sidebar-panel {'):]:
    content = content.replace(
        '.sidebar-panel {\n    flex: 1;',
        '.sidebar-panel {\n    flex: 1;\n    min-height: 0;'
    )

# Fix chat-messages
if 'min-height: 0;' not in content[content.find('.chat-messages {'):]:
    content = content.replace(
        '.chat-messages {\n    padding: 20px;',
        '.chat-messages {\n    padding: 20px;\n    min-height: 0;'
    )

with open('frontend/css/styles.css', 'w') as f:
    f.write(content)
