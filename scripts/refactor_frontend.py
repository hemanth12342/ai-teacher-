import os
import glob
import re

frontend_dir = "frontend"
html_files = glob.glob(os.path.join(frontend_dir, "*.html"))
js_files = glob.glob(os.path.join(frontend_dir, "js", "*.js"))

# 1. Inject config.js into HTML files
for file_path in html_files:
    with open(file_path, "r") as f:
        content = f.read()
    
    if '<script src="/js/config.js"></script>' not in content:
        content = content.replace("</head>", '    <script src="/js/config.js"></script>\n</head>')
    
    # 2. Replace fetch("/api/...") with fetch(window.API_BASE_URL + "/api/...")
    content = content.replace('fetch("/api/', 'fetch(window.API_BASE_URL + "/api/')
    content = content.replace("fetch('/api/", "fetch(window.API_BASE_URL + '/api/")
    content = content.replace('fetch(`/api/', 'fetch(`${window.API_BASE_URL}/api/')
    
    # 3. Replace WebSocket in classroom.html
    # ws = new WebSocket(`${proto}://${location.host}/ws/${roomId}?token=${token}`);
    content = content.replace(
        'ws = new WebSocket(`${proto}://${location.host}/ws/',
        'ws = new WebSocket(`${window.WS_BASE_URL}/ws/'
    )
    
    with open(file_path, "w") as f:
        f.write(content)

# 4. Replace WebSocket in subtitles.js
for file_path in js_files:
    if "subtitles.js" in file_path:
        with open(file_path, "r") as f:
            content = f.read()
        # Original: const url = `${proto}://${location.host}/ws/subtitles/${this.roomId}?token=${this.token}`;
        content = content.replace(
            'const url = `${proto}://${location.host}/ws/subtitles/',
            'const url = `${window.WS_BASE_URL}/ws/subtitles/'
        )
        with open(file_path, "w") as f:
            f.write(content)

print("Refactoring complete.")
