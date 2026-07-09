import re

css_path = 'frontend/css/styles.css'
with open(css_path, 'r') as f:
    css = f.read()

# 1. Rename .sidebar-content to .sidebar-panel and make it flex
css = css.replace(
    '.sidebar-content {\n    flex: 1;\n    overflow-y: auto;\n    position: relative;\n    display: none;\n}',
    '.sidebar-panel {\n    flex: 1;\n    display: none;\n    flex-direction: column;\n    overflow: hidden;\n    height: 100%;\n}'
)
css = css.replace('.sidebar-content.active { display: block; }', '.sidebar-panel.active { display: flex; }')

# 2. Rename .chat-list to .chat-messages
css = css.replace('.chat-list {', '.chat-messages {')
# and change min-height to overflow-y: auto
css = css.replace(
    '    min-height: 100%;\n}',
    '    overflow-y: auto;\n}'
)

# 3. Update .chat-msg to row layout
css = css.replace(
    '.chat-msg {\n    display: flex;\n    flex-direction: column;\n    max-width: 90%;\n}',
    '.chat-msg {\n    display: flex;\n    flex-direction: row;\n    gap: 8px;\n    max-width: 95%;\n}'
)
css = css.replace(
    '.chat-msg.self { align-self: flex-end; }',
    '.chat-msg.self { align-self: flex-end; flex-direction: row-reverse; }'
)

# 4. Add .chat-avatar if it doesn't exist
if '.chat-avatar' not in css:
    avatar_css = """
.chat-avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--accent-fuchsia), var(--accent-indigo));
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    font-weight: bold;
    flex-shrink: 0;
}
.chat-msg-name {
    font-size: 0.75rem;
    color: var(--text-muted);
    margin-bottom: 4px;
    font-weight: 600;
}
.chat-msg-time {
    font-size: 0.65rem;
    color: rgba(255,255,255,0.4);
    margin-top: 4px;
    text-align: right;
}
"""
    css = css.replace('/* -- Chat list -- */', '/* -- Chat list -- */' + avatar_css)

with open(css_path, 'w') as f:
    f.write(css)

print("CSS updated.")
