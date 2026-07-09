css_append = """
/* ═══════════════════════════════════════════════════════
   SUBTITLES OVERLAY
══════════════════════════════════════════════════════ */
.subtitle-overlay {
    position: absolute;
    bottom: 24px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 100;
    pointer-events: none;
    width: 80%;
    text-align: center;
}

.subtitle-text {
    display: inline-block;
    background: rgba(0, 0, 0, 0.75);
    color: #fff;
    font-size: 1.25rem;
    padding: 10px 24px;
    border-radius: 999px;
    opacity: 0;
    transition: opacity 0.3s;
    backdrop-filter: blur(8px);
    text-shadow: 0 2px 4px rgba(0,0,0,0.8);
    font-family: var(--font-display);
    font-weight: 500;
    letter-spacing: 0.02em;
}
.subtitle-text.visible {
    opacity: 1;
}

.subtitle-toggle-wrap {
    display: flex;
    align-items: center;
    gap: 8px;
}
.toggle-label {
    font-size: 0.75rem;
    color: var(--text-muted);
    font-weight: 600;
    text-transform: uppercase;
}

/* ═══════════════════════════════════════════════════════
   Q&A PANEL
══════════════════════════════════════════════════════ */
.qa-panel {
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.qa-track {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: var(--radius-md);
    padding: 16px;
    transition: all var(--transition);
}
.qa-track:hover {
    background: rgba(255, 255, 255, 0.04);
}

.qa-track-header {
    font-family: var(--font-display);
    font-size: 0.85rem;
    font-weight: 700;
    color: var(--accent-cyan);
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.qa-track.teacher .qa-track-header {
    color: var(--accent-fuchsia);
}

.qa-track-body {
    font-size: 0.95rem;
    color: var(--text-primary);
    line-height: 1.6;
}

.qa-input-area {
    display: flex;
    gap: 12px;
    background: rgba(3, 7, 18, 0.95);
}

.qa-input {
    flex: 1;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 999px;
    padding: 12px 20px;
    color: var(--text-primary);
    font-family: var(--font-body);
    font-size: 0.95rem;
    outline: none;
    transition: all var(--transition);
}
.qa-input:focus {
    border-color: var(--accent-fuchsia);
    background: rgba(255, 255, 255, 0.05);
}

.btn-ask {
    background: linear-gradient(135deg, var(--accent-fuchsia), var(--accent-indigo));
    color: white;
    border: none;
    padding: 0 24px;
    border-radius: 999px;
    font-weight: bold;
    cursor: pointer;
    transition: all var(--bounce);
    font-family: var(--font-display);
    box-shadow: 0 4px 16px rgba(232, 121, 249, 0.3);
}
.btn-ask:hover {
    transform: scale(1.05);
    box-shadow: 0 8px 24px rgba(232, 121, 249, 0.5);
}

/* ═══════════════════════════════════════════════════════
   FILES PANEL
══════════════════════════════════════════════════════ */
.files-panel {
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 20px;
    height: 100%;
}

.file-upload-area {
    background: rgba(255, 255, 255, 0.02);
    border: 2px dashed rgba(255, 255, 255, 0.1);
    border-radius: var(--radius-lg);
    padding: 30px 20px;
    text-align: center;
    cursor: pointer;
    transition: all var(--transition);
}
.file-upload-area:hover, .file-upload-area.drag-over {
    background: rgba(232, 121, 249, 0.05);
    border-color: var(--accent-fuchsia);
}

.file-upload-icon {
    font-size: 2.5rem;
    margin-bottom: 12px;
}
.file-upload-text {
    font-size: 1rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 4px;
}
.file-upload-sub {
    font-size: 0.8rem;
    color: var(--text-muted);
}

.file-list {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.file-item {
    display: flex;
    align-items: center;
    gap: 16px;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.05);
    padding: 16px;
    border-radius: var(--radius-md);
    transition: all var(--transition);
}
.file-item:hover {
    background: rgba(255, 255, 255, 0.05);
    border-color: rgba(255, 255, 255, 0.1);
}

.file-icon {
    font-size: 1.8rem;
}
.file-info {
    flex: 1;
    overflow: hidden;
}
.file-name {
    font-weight: 600;
    font-size: 0.95rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    color: var(--text-primary);
    margin-bottom: 4px;
}
.file-meta {
    font-size: 0.75rem;
    color: var(--text-muted);
}
.btn-file-dl {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 50%;
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-primary);
    text-decoration: none;
    transition: all var(--bounce);
    font-size: 1.2rem;
}
.btn-file-dl:hover {
    background: var(--accent-fuchsia);
    color: white;
    transform: scale(1.1);
    box-shadow: 0 4px 12px rgba(232, 121, 249, 0.4);
}

/* ═══════════════════════════════════════════════════════
   PEOPLE / ATTENDANCE PANEL
══════════════════════════════════════════════════════ */
.participants-panel {
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.participant-item {
    display: flex;
    align-items: center;
    gap: 16px;
    background: rgba(255, 255, 255, 0.02);
    border-radius: var(--radius-md);
    padding: 12px 16px;
    border: 1px solid rgba(255,255,255,0.05);
    transition: all var(--transition);
}
.participant-item:hover {
    background: rgba(255,255,255,0.04);
}
.participant-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--accent-amber), var(--accent-rose));
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    color: white;
    font-size: 1rem;
    font-family: var(--font-display);
}
.participant-item > div {
    flex: 1;
}
.participant-name {
    font-weight: 700;
    font-size: 0.95rem;
    color: var(--text-primary);
    margin-bottom: 2px;
}
.participant-role {
    font-size: 0.75rem;
    color: var(--text-muted);
}
.role-badge {
    font-size: 0.7rem;
    padding: 4px 10px;
    border-radius: 999px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.role-teacher {
    background: rgba(232, 121, 249, 0.15);
    color: var(--accent-fuchsia);
    border: 1px solid rgba(232, 121, 249, 0.3);
}
.role-student {
    background: rgba(52, 211, 153, 0.15);
    color: var(--accent-emerald);
    border: 1px solid rgba(52, 211, 153, 0.3);
}
"""

with open('frontend/css/styles.css', 'a') as f:
    f.write("\n" + css_append)

print("CSS appended.")
