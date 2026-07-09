/**
 * Live subtitle module.
 * Captures mic audio via MediaRecorder, streams chunks to /ws/subtitles/{room_id},
 * and renders returned text as an overlay on the video.
 */
class SubtitleManager {
    constructor(roomId, token, subtitleEl) {
        this.roomId = roomId;
        this.token = token;
        this.subtitleEl = subtitleEl;
        this.ws = null;
        this.recorder = null;
        this.active = false;
        this._hideTimer = null;
    }

    start(stream) {
        if (this.active) return;
        try {
            this._connectWS();
            this._startRecording(stream);
            this.active = true;
        } catch (e) {
            console.warn("Subtitle start failed:", e);
        }
    }

    stop() {
        this.active = false;
        this.recorder?.stop();
        this.ws?.close();
        this.recorder = null;
        this.ws = null;
        this._hideSubtitle();
    }

    _connectWS() {
        const proto = location.protocol === "https:" ? "wss" : "ws";
        const url = `${window.WS_BASE_URL}/ws/subtitles/${this.roomId}?token=${this.token}`;
        this.ws = new WebSocket(url);
        this.ws.onmessage = (ev) => {
            try {
                const data = JSON.parse(ev.data);
                if (data.text) this._showSubtitle(data.text);
            } catch { }
        };
    }

    _startRecording(stream) {
        if (!stream || !window.MediaRecorder) return;
        const options = { mimeType: "audio/webm;codecs=opus" };
        try {
            this.recorder = new MediaRecorder(stream, options);
        } catch {
            this.recorder = new MediaRecorder(stream);
        }
        this.recorder.ondataavailable = async (e) => {
            if (e.data.size > 0 && this.ws?.readyState === WebSocket.OPEN) {
                const buf = await e.data.arrayBuffer();
                this.ws.send(buf);
            }
        };
        this.recorder.start(2000); // 2s chunks
    }

    _showSubtitle(text) {
        this.subtitleEl.textContent = text;
        this.subtitleEl.classList.add("visible");
        clearTimeout(this._hideTimer);
        this._hideTimer = setTimeout(() => this._hideSubtitle(), 5000);
    }

    _hideSubtitle() {
        this.subtitleEl.classList.remove("visible");
    }
}