/**
 * Chat + file sharing module.
 */
class ChatManager {
    constructor(containerId, inputId, username) {
        this.container = document.getElementById(containerId);
        this.input = document.getElementById(inputId);
        this.username = username;
        this.onSend = null;    // callback(text)
    }

    // ── Message rendering ─────────────────────────────────

    appendMessage({ sender, sender_role, payload, timestamp }) {
        const text = payload?.text || "";
        const isOwn = sender === this.username;
        const isSystem = !sender;
        const time = new Date(timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

        if (isSystem || sender === "system") {
            this._appendSystem(text);
            return;
        }

        const el = document.createElement("div");
        el.className = `chat-msg${isOwn ? " own" : ""}`;
        const initials = (sender || "?").split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase();
        el.innerHTML = `
      <div class="chat-avatar" title="${this._esc(sender_role || "student")}">${initials}</div>
      <div>
        <div class="chat-bubble">
          ${isOwn ? "" : `<div class="chat-msg-name">${this._esc(sender)}</div>`}
          <div class="chat-msg-text">${this._renderText(text)}</div>
          <div class="chat-msg-time">${time}</div>
        </div>
      </div>`;
        this.container.appendChild(el);
        this._scrollDown();
    }

    appendFileMessage({ sender, payload }) {
        const el = document.createElement("div");
        el.className = "chat-msg";
        const initials = (sender || "?").split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase();
        const icon = this._fileIcon(payload?.name || "");
        el.innerHTML = `
      <div class="chat-avatar">${initials}</div>
      <div>
        <div class="chat-bubble">
          <div class="chat-msg-name">${this._esc(sender)}</div>
          <div style="display:flex;align-items:center;gap:8px;margin-top:4px">
            <span style="font-size:1.1rem">${icon}</span>
            <a href="${payload?.url || "#"}" target="_blank"
               style="font-size:0.8rem;color:var(--accent-indigo2)">
              ${this._esc(payload?.name || "file")}
            </a>
          </div>
        </div>
      </div>`;
        this.container.appendChild(el);
        this._scrollDown();
    }

    _appendSystem(text) {
        const el = document.createElement("div");
        el.className = "system-msg";
        el.textContent = text;
        this.container.appendChild(el);
        this._scrollDown();
    }

    // ── File list rendering ───────────────────────────────

    static renderFileItem(file) {
        const icon = ChatManager.prototype._fileIcon(file.name || "");
        const size = ChatManager._fmtSize(file.size || 0);
        const date = file.uploaded_at ? new Date(file.uploaded_at).toLocaleDateString() : "";
        return `
      <div class="file-item">
        <span class="file-icon">${icon}</span>
        <div class="file-info">
          <div class="file-name">${file.name || "unknown"}</div>
          <div class="file-meta">${size} · ${file.uploaded_by || "?"} · ${date}</div>
        </div>
        <a href="${file.url || "#"}" target="_blank" class="btn-file-dl" title="Download">⬇</a>
      </div>`;
    }

    // ── Helpers ───────────────────────────────────────────

    _renderText(text) {
        // URL detection
        const urlRx = /https?:\/\/[^\s<>"]+/g;
        const esc = this._esc(text);
        return esc.replace(urlRx, url => `<a href="${url}" target="_blank">${url}</a>`);
    }

    _fileIcon(name) {
        const ext = (name.split(".").pop() || "").toLowerCase();
        const map = {
            pdf: "📄", docx: "📝", doc: "📝", xlsx: "📊", xls: "📊",
            txt: "📃", png: "🖼", jpg: "🖼", jpeg: "🖼", gif: "🖼",
            mp4: "🎬", mp3: "🎵", zip: "🗜"
        };
        return map[ext] || "📎";
    }

    static _fmtSize(b) {
        if (b < 1024) return b + " B";
        if (b < 1048576) return (b / 1024).toFixed(1) + " KB";
        return (b / 1048576).toFixed(1) + " MB";
    }

    _esc(s) {
        return String(s || "").replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
    }

    _scrollDown() {
        this.container.scrollTop = this.container.scrollHeight;
    }
}