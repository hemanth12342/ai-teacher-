/**
 * Q&A dual-panel module.
 * Left (indigo): teacher slot  |  Right (cyan): AI streaming answer
 */
class QAManager {
    constructor({ teacherBodyId, aiBodyId, inputId, sendBtnId, sourcesId }) {
        this.teacherBody = document.getElementById(teacherBodyId);
        this.aiBody = document.getElementById(aiBodyId);
        this.input = document.getElementById(inputId);
        this.sendBtn = document.getElementById(sendBtnId);
        this.sources = document.getElementById(sourcesId);
        this.onQuestion = null;   // callback(question)
        this._setupSend();
    }

    _setupSend() {
        this.sendBtn?.addEventListener("click", () => this._send());
        this.input?.addEventListener("keydown", e => {
            if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); this._send(); }
        });
    }

    _send() {
        const q = (this.input?.value || "").trim();
        if (!q) return;
        this.input.value = "";
        this.showThinking(q);
        if (this.onQuestion) this.onQuestion(q);
    }

    showThinking(question) {
        if (this.teacherBody) {
            this.teacherBody.innerHTML = `<em style="color:var(--text-muted)">Q: ${this._esc(question)}</em><br>
        <span style="color:var(--text-muted);font-size:0.78rem">Waiting for teacher response…</span>`;
        }
        if (this.aiBody) {
            this.aiBody.innerHTML = `
        <div style="color:var(--text-muted);font-size:0.78rem;margin-bottom:8px">Asking AI…</div>
        <div class="qa-typing">
          <div class="qa-dot"></div><div class="qa-dot"></div><div class="qa-dot"></div>
        </div>`;
        }
    }

    showAnswer({ question, ai_answer, sources, teacher_note }) {
        if (this.teacherBody) {
            this.teacherBody.innerHTML =
                `<div class="md-content">${this._md(
                    teacher_note ||
                    `*Q: ${question}*\n\n_Teacher has not responded yet._`
                )}</div>`;
        }
        if (this.aiBody) {
            this.aiBody.innerHTML = `<div class="md-content">${this._md(ai_answer || "_No answer_")}</div>`;
        }
        if (this.sources && sources?.length) {
            this.sources.innerHTML =
                "📎 Sources: " + sources.map(s => `<span class="qa-source-tag">${this._esc(s)}</span>`).join("");
            this.sources.style.display = "block";
        }
    }

    showTeacherNote(note) {
        if (this.teacherBody) {
            this.teacherBody.innerHTML = `<div class="md-content">${this._md(note)}</div>`;
        }
    }

    // ── Minimal Markdown → HTML ───────────────────────────
    _md(text) {
        return text
            // code blocks
            .replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, code) =>
                `<pre><code class="${lang}">${this._esc(code.trim())}</code></pre>`)
            // inline code
            .replace(/`([^`]+)`/g, (_, c) => `<code>${this._esc(c)}</code>`)
            // bold
            .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
            // italic
            .replace(/\*(.+?)\*/g, "<em>$1</em>")
            // headings
            .replace(/^### (.+)$/gm, "<h3>$1</h3>")
            .replace(/^## (.+)$/gm, "<h2>$1</h2>")
            .replace(/^# (.+)$/gm, "<h1>$1</h1>")
            // unordered list
            .replace(/^[-*] (.+)$/gm, "<li>$1</li>")
            // blockquote
            .replace(/^> (.+)$/gm, "<blockquote>$1</blockquote>")
            // horizontal rule
            .replace(/^---$/gm, "<hr>")
            // paragraphs / line breaks
            .replace(/\n{2,}/g, "</p><p>")
            .replace(/\n/g, "<br>")
            .replace(/^(.+)$/, "<p>$1</p>")
            // wrap list items
            .replace(/(<li>.*<\/li>\n?)+/g, m => `<ul>${m}</ul>`);
    }

    _esc(s) {
        return String(s || "").replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
    }
}