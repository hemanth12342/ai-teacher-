with open('frontend/classroom.html', 'r') as f:
    content = f.read()

# Add tab button
tab_html = '<button class="sidebar-tab" data-panel="cams" onclick="switchTab(\'cams\')">📷 Webcams</button>'
if 'data-panel="cams"' not in content:
    content = content.replace(
        '<button class="sidebar-tab" data-panel="people" onclick="switchTab(\'people\')">👥 People</button>',
        '<button class="sidebar-tab" data-panel="people" onclick="switchTab(\'people\')">👥 People</button>\n                ' + tab_html
    )

# Add panel
panel_html = '''
            <!-- Webcams panel -->
            <div class="sidebar-panel" id="panel-cams">
                <div class="student-video-grid" id="student-video-grid" style="flex:1; overflow-y:auto; padding:16px; display:flex; flex-direction:column; gap:16px; min-height:0;">
                </div>
            </div>
'''
if 'id="panel-cams"' not in content:
    content = content.replace(
        '<!-- Chat panel -->',
        panel_html + '\n            <!-- Chat panel -->'
    )

# Update addVideoTile
new_add_video = '''
        function addVideoTile(peerId, stream, label, roleStr) {
            if (document.getElementById(`tile-${peerId}`)) return;
            const tile = document.createElement("div");
            tile.className = "video-tile";
            tile.id = `tile-${peerId}`;
            const vid = document.createElement("video");
            vid.autoplay = vid.playsInline = true;
            vid.srcObject = stream;
            const lbl = document.createElement("div");
            lbl.className = "video-tile-label";
            lbl.textContent = label || peerId;
            tile.append(vid, lbl);
            
            const isStudent = roleStr === "student";
            if (isStudent) tile.style.minHeight = "200px";
            const targetGrid = isStudent ? document.getElementById("student-video-grid") : document.getElementById("video-grid");
            targetGrid.appendChild(tile);
            
            if (!isStudent) updateGridLayout();
        }
'''
import re
content = re.sub(
    r'function addVideoTile\(peerId, stream, label\) \{[\s\S]*?updateGridLayout\(\);\n        \}',
    new_add_video.strip(),
    content
)

# Update WebRTC callback
new_cb = '''
                (peerId, stream) => {
                    const part = attendanceMgr.participants.find(p => p.id === peerId);
                    addVideoTile(peerId, stream, part?.name || peerId, part?.role || "student");
                },
'''
content = re.sub(
    r'\(peerId, stream\) => addVideoTile\(peerId, stream, remotePeers\[peerId\]\?\.username \|\| peerId\),',
    new_cb.strip() + ',',
    content
)

# Update init() to move local video if student
if 'document.getElementById("student-video-grid").appendChild(localTile);' not in content:
    content = content.replace(
        'document.getElementById("local-label").textContent = `${username} (You)`;',
        'document.getElementById("local-label").textContent = `${username} (You)`;\n            if (role === "student") {\n                const localTile = document.getElementById("tile-local");\n                localTile.style.minHeight = "200px";\n                document.getElementById("student-video-grid").appendChild(localTile);\n                updateGridLayout();\n            }'
    )

with open('frontend/classroom.html', 'w') as f:
    f.write(content)
