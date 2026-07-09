/**
 * Attendance tracking module (client side).
 * Tracks join time and renders participant list.
 */
class AttendanceManager {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.participants = {};  // peer_id → {username, role, joinedAt}
    }

    addParticipant(peerId, username, role) {
        this.participants[peerId] = { username, role, joinedAt: Date.now() };
        this._render();
    }

    removeParticipant(peerId) {
        delete this.participants[peerId];
        this._render();
    }

    updateAll(participants) {
        // participants: [{peer_id, username, role}]
        const incoming = new Set(participants.map(p => p.peer_id));
        // Remove stale
        Object.keys(this.participants).forEach(id => {
            if (!incoming.has(id)) delete this.participants[id];
        });
        // Add new
        participants.forEach(p => {
            if (!this.participants[p.peer_id]) {
                this.participants[p.peer_id] = {
                    username: p.username, role: p.role, joinedAt: Date.now()
                };
            }
        });
        this._render();
    }

    _render() {
        if (!this.container) return;
        const entries = Object.entries(this.participants).sort((a, b) => a[1].joinedAt - b[1].joinedAt);
        if (!entries.length) {
            this.container.innerHTML = `<div style="text-align:center;color:var(--text-muted);padding:30px;font-size:0.82rem">No participants yet</div>`;
            return;
        }
        let studentCount = 0;
        this.container.innerHTML = entries.map(([id, p]) => {
            const initials = (p.username || "?").split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase();
            const elapsed = this._elapsed(p.joinedAt);
            let displayNumber = "";
            if (p.role === "student") {
                studentCount++;
                displayNumber = `<span style="font-size:0.75rem; color: var(--text-muted); margin-right: 6px;">#${studentCount}</span>`;
            }
            return `
        <div class="participant-item">
          <div class="participant-avatar">${initials}</div>
          <div>
            <div class="participant-name">${displayNumber}${this._esc(p.username)}</div>
            <div class="participant-role">Joined ${elapsed} ago</div>
          </div>
          <span class="role-badge ${p.role === "teacher" ? "role-teacher" : "role-student"}">
            ${p.role === "teacher" ? "👩‍🏫 Teacher" : "🎓 Student"}
          </span>
        </div>`;
        }).join("");
    }

    _elapsed(ts) {
        const s = Math.floor((Date.now() - ts) / 1000);
        if (s < 60) return `${s}s`;
        if (s < 3600) return `${Math.floor(s / 60)}m`;
        return `${Math.floor(s / 3600)}h ${Math.floor((s % 3600) / 60)}m`;
    }

    _esc(s) {
        return String(s || "").replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
    }
}